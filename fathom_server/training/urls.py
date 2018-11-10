from django.conf.urls import url

from fathom_server.training import views


urlpatterns = [
    url(r'webpages/(\d+)/', views.view_frozen_webpage, name='view-frozen-webpage'),
]
