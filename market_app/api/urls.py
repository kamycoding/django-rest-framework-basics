from django.urls import path

from .views import markets_view

urlpatterns = [
    path('market/', markets_view, name='market-list'),
]
