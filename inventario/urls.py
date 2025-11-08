"""
URLs para la aplicación Inventario
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductoViewSet, LoteViewSet, MovimientoInventarioViewSet

# Crear router y registrar viewsets
router = DefaultRouter()
router.register(r'productos', ProductoViewSet, basename='producto')
router.register(r'lotes', LoteViewSet, basename='lote')
router.register(r'movimientos', MovimientoInventarioViewSet, basename='movimiento')

urlpatterns = [
    path('', include(router.urls)),
]
