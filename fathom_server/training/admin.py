import json
import os
from tempfile import mkstemp

from marionette_driver.marionette import Marionette

from django.conf import settings
from django.conf.urls import url
from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, redirect

from fathom_server.training import models


@admin.register(models.Fact)
class FactAdmin(admin.ModelAdmin):
    pass


@admin.register(models.FactSet)
class FactSetAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Ruleset)
class RulesetAdmin(admin.ModelAdmin):
    pass


class WebpageFactInline(admin.TabularInline):
    model = models.WebpageFact
    fields = ['fact', 'fact_answer']


@admin.register(models.Webpage)
class WebpageAdmin(admin.ModelAdmin):
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


@admin.register(models.TrainingRun)
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
        training_run = get_object_or_404(models.TrainingRun, id=run_id)

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
