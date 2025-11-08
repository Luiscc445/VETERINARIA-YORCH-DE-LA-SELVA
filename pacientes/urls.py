"""
URLs para la aplicación Pacientes
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EspecieViewSet, RazaViewSet, MascotaViewSet

# Crear router y registrar viewsets
router = DefaultRouter()
router.register(r'especies', EspecieViewSet, basename='especie')
router.register(r'razas', RazaViewSet, basename='raza')
router.register(r'mascotas', MascotaViewSet, basename='mascota')

urlpatterns = [
    path('', include(router.urls)),
]
