import json
import os
import random
from tempfile import mkstemp

from marionette_driver.marionette import Marionette

from django import forms
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, redirect, render

from fathom_server.training.models import (
    Fact,
    FactSet,
    Ruleset,
    TrainingRun,
    Webpage,
    WebpageFact,
)


@admin.register(Fact)
class FactAdmin(admin.ModelAdmin):
    pass


class WebpageFactForm(forms.ModelForm):
    class Meta:
        model = WebpageFact
        fields = ['fact_answer']


@admin.register(FactSet)
class FactSetAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super(FactSetAdmin, self).get_urls()
        extra_urls = [
            url(
                r'^(\d+)/fill/$',
                self.admin_site.admin_view(self.fill),
                name='fill_factset',
            ),
            url(
                r'^(\d+)/fill/(\d+)/$',
                self.admin_site.admin_view(self.fill_form),
                name='fill_factset_form',
            ),
        ]
        return extra_urls + urls

    def get_unanswered_webpage(self, facts):
        # Find webpages who are missing answers for all the facts
        answered_webpages = Webpage.objects.all()
        for fact in facts:
            answered_webpages = answered_webpages.filter(webpagefact__fact=fact)

        # Exclude answered webpages so we only find webpages that are
        # missing answers.
        unanswered_webpages = Webpage.objects.exclude(
            id__in=[webpage.id for webpage in answered_webpages]
        ).exclude(frozen_html='')

        return random.choice(unanswered_webpages)

    def fill(self, request, factset_id):
        factset = get_object_or_404(FactSet, id=factset_id)
        facts = factset.facts.all()
        webpage = self.get_unanswered_webpage(facts)
        return redirect('admin:fill_factset_form', factset_id, webpage.id)

    def fill_form(self, request, factset_id, webpage_id):
        request.current_app = self.admin_site.name

        factset = get_object_or_404(FactSet, id=factset_id)
        facts = factset.facts.all()
        webpage = get_object_or_404(Webpage, id=webpage_id)

        # Supply existing webpage facts to the forms if any are found
        webpage_facts = list(webpage.webpagefact_set.filter(fact__in=facts))
        present_facts = [webpage_fact.fact for webpage_fact in webpage_facts]
        for fact in facts:
            if fact not in present_facts:
                webpage_facts.append(WebpageFact(webpage=webpage, fact=fact))

        forms = [
            WebpageFactForm(
                request.POST if request.method == 'POST' else None,
                prefix=webpage_fact.fact.id,
                instance=webpage_fact,
            )
            for webpage_fact in webpage_facts
        ]

        if request.method == 'POST' and all([form.is_valid() for form in forms]):
            for form in forms:
                form.save()
            return redirect('admin:fill_factset', factset_id)

        return render(request, 'admin/training/factset/fill.html', {
            'factset': factset,
            'webpage': webpage,
            'forms': forms,
        })


@admin.register(Ruleset)
class RulesetAdmin(admin.ModelAdmin):
    pass


class WebpageFactInline(admin.TabularInline):
    model = WebpageFact
    fields = ['fact', 'fact_answer']


@admin.register(Webpage)
class WebpageAdmin(admin.ModelAdmin):
    list_display = ['url', 'short_frozen_html']
    fields = ['url', 'short_frozen_html']
    readonly_fields = ['short_frozen_html']
    actions = ['freeze', 'train']
    inlines = [WebpageFactInline]

    def short_frozen_html(self, webpage):
        return webpage.frozen_html[:200]

    def freeze(self, request, queryset):
        with open(os.path.join(settings.BASE_DIR, 'build', 'freeze.bundle.js')) as f:
            freeze_script = f.read()

        client = None
        try:
            client = Marionette(bin=settings.FIREFOX_BIN, headless=True)
            client.start_session()

            for webpage in queryset:
                print('Freezing {}...'.format(webpage.url))
                client.navigate(webpage.url)
                results = client.execute_async_script(
                    freeze_script,
                    script_timeout=1000 * 60 * 5,
                )
                webpage.frozen_html = results['html']
                webpage.save()
        finally:
            if client:
                client.cleanup()


@admin.register(TrainingRun)
class TrainingRunModelAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super(TrainingRunModelAdmin, self).get_urls()
        extra_urls = [
            url(
                r'^(\d+)/train/$',
                self.admin_site.admin_view(self.train),
                name='execute_training_run',
            ),
        ]
        return extra_urls + urls

    def train(self, request, run_id):
        training_run = get_object_or_404(TrainingRun, id=run_id)

        with open(os.path.join(settings.BASE_DIR, 'build', 'train.bundle.js')) as f:
            train_script = f.read()

        fd, ruleset_path = mkstemp()
        with os.fdopen(fd, 'w') as f:
            f.write(training_run.ruleset.code.encode('utf8'))

        facts = training_run.ruleset.fact_set.facts.all()

        client = None
        try:
            client = Marionette(bin=settings.FIREFOX_BIN, headless=True)
            client.start_session()

            webpages = list(map(
                lambda webpage: {
                    'url': webpage.url,
                    'facts': {
                        fact.fact.key: fact.fact_answer
                        for fact in webpage.webpagefact_set.filter(fact__in=facts)
                    },
                },
                training_run.training_pages.all(),
            ))

            results = client.execute_async_script(
                train_script,
                script_args=(
                    ruleset_path,
                    os.path.join(settings.BASE_DIR, 'build', 'train_framescript.bundle.js'),
                    list(map(lambda fact: fact.key, facts)),
                    webpages,
                    json.loads(training_run.initial_coefficients),
                ),
                sandbox='system',
                script_timeout=1000 * 60 * 5,
            )

            training_run.final_coefficients = json.dumps(results[0])
            training_run.save()
        finally:
            if client:
                client.cleanup()
            os.remove(ruleset_path)

        messages.add_message(request, messages.SUCCESS, 'Training run completed.')
        return redirect('admin:training_trainingrun_change', run_id)
