import os

from marionette_driver.marionette import Marionette

from django.conf import settings
from django.contrib import admin

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
    actions = ['freeze']
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
    pass
