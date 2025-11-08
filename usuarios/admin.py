"""
Configuración del Admin para la aplicación Usuarios
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Configuración personalizada del panel de administración para usuarios
    """

    # Campos a mostrar en la lista de usuarios
    list_display = (
        'username',
        'email',
        'get_nombre_completo',
        'rol_badge',
        'telefono',
        'is_active',
        'is_staff',
        'fecha_registro'
    )

    # Filtros laterales
    list_filter = (
        'rol',
        'is_staff',
        'is_superuser',
        'is_active',
        'fecha_registro'
    )

    # Campos de búsqueda
    search_fields = (
        'username',
        'first_name',
        'last_name',
        'email',
        'telefono',
        'cedula_profesional'
    )

    # Ordenamiento por defecto
    ordering = ('-fecha_registro',)

    # Campos editables en línea
    list_editable = ('is_active',)

    # Configuración de fieldsets para el formulario de edición
    fieldsets = (
        ('Información de Acceso', {
            'fields': ('username', 'password')
        }),
        ('Información Personal', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'telefono',
                'direccion',
                'fecha_nacimiento',
                'foto_perfil'
            )
        }),
        ('Rol y Permisos', {
            'fields': (
                'rol',
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
        ('Información Profesional (Solo Médicos)', {
            'fields': ('cedula_profesional', 'especialidad'),
            'classes': ('collapse',)
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'date_joined', 'fecha_registro', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    # Campos para crear un nuevo usuario
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'password1',
                'password2',
                'first_name',
                'last_name',
                'rol',
                'telefono'
            ),
        }),
    )

    # Campos de solo lectura
    readonly_fields = ('fecha_registro', 'fecha_actualizacion', 'last_login', 'date_joined')

    def get_nombre_completo(self, obj):
        """Retorna el nombre completo del usuario"""
        return obj.get_full_name() or '-'
    get_nombre_completo.short_description = 'Nombre Completo'

    def rol_badge(self, obj):
        """Muestra el rol con un badge de color"""
        colors = {
            'TUTOR': '#17a2b8',      # Info blue
            'MEDICO': '#28a745',     # Success green
            'RECEPCION': '#ffc107',  # Warning yellow
            'ADMIN': '#dc3545',      # Danger red
        }
        color = colors.get(obj.rol, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_rol_display()
        )
    rol_badge.short_description = 'Rol'

    def get_queryset(self, request):
        """Optimiza las consultas"""
        return super().get_queryset(request).select_related()
