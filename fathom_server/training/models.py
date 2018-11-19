from hashlib import sha256

from django.db import models
from django.urls import reverse


class Fact(models.Model):
    TYPE_STRING = 'string'
    TYPE_NUMBER = 'number'
    TYPE_BOOLEAN = 'boolean'

    key = models.CharField(max_length=255, unique=True)
    question = models.TextField()
    type = models.CharField(max_length=255, choices=(
        (TYPE_STRING, 'String'),
        (TYPE_NUMBER, 'Number'),
        (TYPE_BOOLEAN, 'Boolean'),
    ))

    def __str__(self):
        return self.question


class FactSet(models.Model):
    name = models.CharField(max_length=255, default='New Factset')
    facts = models.ManyToManyField(Fact)

    def __str__(self):
        return self.name


class Ruleset(models.Model):
    name = models.CharField(max_length=255, default='New Ruleset')
    code = models.TextField()
    fact_set = models.ForeignKey(FactSet, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name


def _frozen_html_upload_to(instance, filename):
    return 'frozen_webpages/{}.html'.format(sha256(instance.url).hexdigest())


class Webpage(models.Model):
    url = models.URLField(unique=True)
    frozen_html = models.FileField(blank=True, upload_to=_frozen_html_upload_to)

    def get_absolute_url(self):
        return reverse('view-frozen-webpage', args=[self.id])

    def __str__(self):
        return self.url


class WebpageFact(models.Model):
    webpage = models.ForeignKey(Webpage, on_delete=models.CASCADE)
    fact = models.ForeignKey(Fact, on_delete=models.CASCADE)
    fact_answer = models.TextField()


class TrainingRun(models.Model):
    ruleset = models.ForeignKey(Ruleset, on_delete=models.CASCADE)
    initial_coefficients = models.TextField(blank=True)
    training_pages = models.ManyToManyField(Webpage, related_name='training_runs', blank=True)
    testing_pages = models.ManyToManyField(Webpage, related_name='testing_runs', blank=True)
    final_coefficients = models.TextField(blank=True)
