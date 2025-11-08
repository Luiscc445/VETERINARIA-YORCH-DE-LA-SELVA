"""
URLs para la aplicación Usuarios
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

# Crear router y registrar viewsets
router = DefaultRouter()
router.register(r'', UserViewSet, basename='usuario')

urlpatterns = [
    path('', include(router.urls)),
]
