"""
URL configuration for RamboPet project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# API Documentation Schema
schema_view = get_schema_view(
    openapi.Info(
        title="RamboPet API",
        default_version='v1',
        description="API para Sistema de Gestión Integral de Clínica Veterinaria RamboPet",
        terms_of_service="https://www.rambopet.com/terms/",
        contact=openapi.Contact(email="contacto@rambopet.com"),
        license=openapi.License(name="Proprietary License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # API v1
    path('api/v1/usuarios/', include('usuarios.urls')),
    path('api/v1/pacientes/', include('pacientes.urls')),
    path('api/v1/citas/', include('citas.urls')),
    path('api/v1/hce/', include('hce.urls')),
    path('api/v1/inventario/', include('inventario.urls')),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize Admin Site
admin.site.site_header = "RamboPet Administración"
admin.site.site_title = "RamboPet Admin"
admin.site.index_title = "Panel de Administración"
