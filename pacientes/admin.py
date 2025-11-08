"""
Configuración del Admin para la aplicación Pacientes
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Especie, Raza, Mascota


@admin.register(Especie)
class EspecieAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para Especies
    """

    list_display = ('nombre', 'cantidad_razas', 'cantidad_mascotas', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)
    list_editable = ('activo',)

    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'descripcion', 'activo')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('fecha_creacion',)

    def cantidad_razas(self, obj):
        """Cuenta el número de razas asociadas"""
        return obj.razas.count()
    cantidad_razas.short_description = 'N° Razas'

    def cantidad_mascotas(self, obj):
        """Cuenta el número de mascotas asociadas"""
        return obj.mascotas.count()
    cantidad_mascotas.short_description = 'N° Mascotas'


class RazaInline(admin.TabularInline):
    """
    Inline para mostrar razas dentro de especies
    """
    model = Raza
    extra = 1
    fields = ('nombre', 'descripcion', 'activo')


@admin.register(Raza)
class RazaAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para Razas
    """

    list_display = ('nombre', 'especie', 'cantidad_mascotas', 'activo', 'fecha_creacion')
    list_filter = ('especie', 'activo', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion', 'especie__nombre')
    ordering = ('especie', 'nombre')
    list_editable = ('activo',)

    fieldsets = (
        ('Información General', {
            'fields': ('especie', 'nombre', 'descripcion', 'activo')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('fecha_creacion',)

    def cantidad_mascotas(self, obj):
        """Cuenta el número de mascotas asociadas"""
        return obj.mascotas.count()
    cantidad_mascotas.short_description = 'N° Mascotas'


@admin.register(Mascota)
class MascotaAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para Mascotas
    """

    list_display = (
        'foto_thumbnail',
        'nombre',
        'especie',
        'raza',
        'sexo_badge',
        'tutor_link',
        'edad',
        'peso_actual',
        'estado_badge',
        'fecha_registro'
    )

    list_filter = (
        'especie',
        'sexo',
        'esterilizado',
        'activo',
        'fallecido',
        'fecha_registro'
    )

    search_fields = (
        'nombre',
        'tutor__first_name',
        'tutor__last_name',
        'tutor__email',
        'microchip'
    )

    ordering = ('-fecha_registro',)

    fieldsets = (
        ('Información del Tutor', {
            'fields': ('tutor',)
        }),
        ('Información Básica', {
            'fields': (
                'nombre',
                'especie',
                'raza',
                'sexo',
                'fecha_nacimiento',
                'foto'
            )
        }),
        ('Características Físicas', {
            'fields': ('color', 'peso_actual', 'microchip')
        }),
        ('Información Médica', {
            'fields': (
                'esterilizado',
                'alergias',
                'condiciones_cronicas',
                'observaciones'
            )
        }),
        ('Estado', {
            'fields': (
                'activo',
                'fallecido',
                'fecha_fallecimiento'
            )
        }),
        ('Fechas de Registro', {
            'fields': ('fecha_registro', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('fecha_registro', 'fecha_actualizacion')

    autocomplete_fields = ['tutor']

    def foto_thumbnail(self, obj):
        """Muestra una miniatura de la foto"""
        if obj.foto:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" />',
                obj.foto.url
            )
        return format_html('<div style="width: 50px; height: 50px; border-radius: 50%; background-color: #ddd;"></div>')
    foto_thumbnail.short_description = 'Foto'

    def tutor_link(self, obj):
        """Muestra el nombre del tutor con enlace"""
        return format_html(
            '<a href="/admin/usuarios/user/{}/change/">{}</a>',
            obj.tutor.id,
            obj.tutor.get_full_name() or obj.tutor.username
        )
    tutor_link.short_description = 'Tutor'

    def sexo_badge(self, obj):
        """Muestra el sexo con un badge de color"""
        colors = {
            'M': '#007bff',  # Azul para macho
            'H': '#e83e8c',  # Rosa para hembra
            'D': '#6c757d',  # Gris para desconocido
        }
        color = colors.get(obj.sexo, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_sexo_display()
        )
    sexo_badge.short_description = 'Sexo'

    def estado_badge(self, obj):
        """Muestra el estado con un badge de color"""
        if obj.fallecido:
            return format_html(
                '<span style="background-color: #343a40; color: white; padding: 3px 10px; '
                'border-radius: 3px;">Fallecido</span>'
            )
        elif obj.activo:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px;">Activo</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 10px; '
                'border-radius: 3px;">Inactivo</span>'
            )
    estado_badge.short_description = 'Estado'

    def edad(self, obj):
        """Muestra la edad aproximada"""
        edad = obj.edad_aproximada
        if edad is not None:
            if edad == 0:
                return "Menos de 1 año"
            elif edad == 1:
                return "1 año"
            else:
                return f"{edad} años"
        return "-"
    edad.short_description = 'Edad'

    def get_queryset(self, request):
        """Optimiza las consultas"""
        return super().get_queryset(request).select_related('tutor', 'especie', 'raza')
