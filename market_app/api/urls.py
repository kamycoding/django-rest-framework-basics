from django.urls import path

from .views import market_single_view, markets_view, sellers_view

urlpatterns = [
    path('market/', markets_view, name='market-list'),
    path('market/<int:pk>/', market_single_view, name='market-detail'),
    path('seller/', sellers_view, name='seller-list'),
]
