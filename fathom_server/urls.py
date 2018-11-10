from django.contrib import admin
from django.conf.urls import include, url


urlpatterns = [
    url('', include('fathom_server.training.urls')),

    url('admin/', admin.site.urls),
]
