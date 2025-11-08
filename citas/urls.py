"""
URLs para la aplicación Citas
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CitaViewSet

# Crear router y registrar viewsets
router = DefaultRouter()
router.register(r'', CitaViewSet, basename='cita')

urlpatterns = [
    path('', include(router.urls)),
]
