"""
URLs para la aplicación HCE
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EpisodioClinicoViewSet, ConstantesVitalesViewSet, AdjuntoViewSet

# Crear router y registrar viewsets
router = DefaultRouter()
router.register(r'episodios', EpisodioClinicoViewSet, basename='episodio')
router.register(r'constantes', ConstantesVitalesViewSet, basename='constantes')
router.register(r'adjuntos', AdjuntoViewSet, basename='adjunto')

urlpatterns = [
    path('', include(router.urls)),
]
