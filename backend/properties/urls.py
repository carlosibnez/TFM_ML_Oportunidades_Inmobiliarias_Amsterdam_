from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PropertyViewSet,
    PropertyImageViewSet,
    MLModelViewSet,
    PredictionViewSet,
    NeighborhoodStatsViewSet
)

router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename='property')
router.register(r'images', PropertyImageViewSet, basename='propertyimage')
router.register(r'ml-models', MLModelViewSet, basename='mlmodel')
router.register(r'predictions', PredictionViewSet, basename='prediction')
router.register(r'neighborhood-stats', NeighborhoodStatsViewSet, basename='neighborhoodstats')

urlpatterns = [
    path('', include(router.urls)),
]
