from django.urls import path

from fathom_server.training import views

urlpatterns = [
    path('webpages/<int:webpage_id>/', views.view_frozen_webpage, name='view-frozen-webpage'),
]
