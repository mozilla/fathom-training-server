from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('fathom_server.training.urls')),

    path('admin/', admin.site.urls),
]
