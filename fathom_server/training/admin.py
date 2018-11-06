from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

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
        with open(settings.BASE_DIR.joinpath('build', 'freeze.bundle.js')) as f:
            freeze_script = f.read()

        driver = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            desired_capabilities=DesiredCapabilities.FIREFOX,
        )
        for webpage in queryset:
            print(f'Freezing {webpage.url}...')
            driver.get(webpage.url)
            results = driver.execute_async_script(freeze_script)
            webpage.frozen_html = results['html']
            webpage.save()
        driver.close()
