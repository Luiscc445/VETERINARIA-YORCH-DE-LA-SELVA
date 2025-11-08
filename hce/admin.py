"""
Configuración del Admin para la aplicación HCE
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import EpisodioClinico, ConstantesVitales, Adjunto


class ConstantesVitalesInline(admin.StackedInline):
    """
    Inline para mostrar constantes vitales dentro del episodio clínico
    """
    model = ConstantesVitales
    extra = 1
    fields = (
        ('peso', 'temperatura'),
        ('frecuencia_cardiaca', 'frecuencia_respiratoria'),
        ('presion_arterial_sistolica', 'presion_arterial_diastolica'),
        ('tiempo_llenado_capilar', 'condicion_corporal'),
        'observaciones',
        ('registrado_por', 'fecha_registro')
    )
    readonly_fields = ('fecha_registro',)


class AdjuntoInline(admin.TabularInline):
    """
    Inline para mostrar adjuntos dentro del episodio clínico
    """
    model = Adjunto
    extra = 1
    fields = ('tipo', 'titulo', 'archivo', 'descripcion')


@admin.register(EpisodioClinico)
class EpisodioClinicoAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para Episodios Clínicos
    """

    list_display = (
        'id',
        'fecha_creacion_formatted',
        'mascota_link',
        'medico_link',
        'diagnostico_preview',
        'pronostico_badge',
        'estado_badge',
        'tiene_constantes',
        'cantidad_adjuntos'
    )

    list_filter = (
        'pronostico',
        'episodio_cerrado',
        'fecha_creacion',
        'medico'
    )

    search_fields = (
        'mascota__nombre',
        'medico__first_name',
        'medico__last_name',
        'motivo_consulta',
        'diagnostico_presuntivo',
        'diagnostico_definitivo',
        'id'
    )

    ordering = ('-fecha_creacion',)

    date_hierarchy = 'fecha_creacion'

    inlines = [ConstantesVitalesInline, AdjuntoInline]

    fieldsets = (
        ('Información del Episodio', {
            'fields': ('cita', 'mascota', 'medico')
        }),
        ('Motivo y Anamnesis', {
            'fields': ('motivo_consulta', 'anamnesis')
        }),
        ('Examen Físico', {
            'fields': ('examen_fisico',)
        }),
        ('Diagnóstico', {
            'fields': ('diagnostico_presuntivo', 'diagnostico_definitivo')
        }),
        ('Tratamiento', {
            'fields': ('plan_tratamiento', 'medicamentos', 'procedimientos')
        }),
        ('Pronóstico y Seguimiento', {
            'fields': ('pronostico', 'indicaciones', 'proxima_revision', 'episodio_cerrado')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')

    autocomplete_fields = ['mascota', 'medico', 'cita']

    def fecha_creacion_formatted(self, obj):
        """Formatea la fecha de creación"""
        return obj.fecha_creacion.strftime('%d/%m/%Y %H:%M')
    fecha_creacion_formatted.short_description = 'Fecha'
    fecha_creacion_formatted.admin_order_field = 'fecha_creacion'

    def mascota_link(self, obj):
        """Muestra el nombre de la mascota con enlace"""
        return format_html(
            '<a href="/admin/pacientes/mascota/{}/change/">{}</a>',
            obj.mascota.id,
            obj.mascota.nombre
        )
    mascota_link.short_description = 'Mascota'

    def medico_link(self, obj):
        """Muestra el nombre del médico con enlace"""
        return format_html(
            '<a href="/admin/usuarios/user/{}/change/">{}</a>',
            obj.medico.id,
            obj.medico.get_full_name() or obj.medico.username
        )
    medico_link.short_description = 'Médico'

    def diagnostico_preview(self, obj):
        """Muestra una vista previa del diagnóstico"""
        diagnostico = obj.diagnostico_definitivo or obj.diagnostico_presuntivo
        if len(diagnostico) > 50:
            return f"{diagnostico[:50]}..."
        return diagnostico
    diagnostico_preview.short_description = 'Diagnóstico'

    def pronostico_badge(self, obj):
        """Muestra el pronóstico con un badge de color"""
        colors = {
            'EXCELENTE': '#28a745',
            'BUENO': '#17a2b8',
            'RESERVADO': '#ffc107',
            'GRAVE': '#dc3545',
        }
        color = colors.get(obj.pronostico, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_pronostico_display()
        )
    pronostico_badge.short_description = 'Pronóstico'

    def estado_badge(self, obj):
        """Muestra el estado del episodio con un badge"""
        if obj.episodio_cerrado:
            return format_html(
                '<span style="background-color: #6c757d; color: white; padding: 3px 10px; '
                'border-radius: 3px;">Cerrado</span>'
            )
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
            'border-radius: 3px;">Activo</span>'
        )
    estado_badge.short_description = 'Estado'

    def tiene_constantes(self, obj):
        """Indica si tiene constantes vitales registradas"""
        if obj.constantes_vitales.exists():
            return format_html('<span style="color: #28a745; font-size: 18px;">✓</span>')
        return format_html('<span style="color: #dc3545; font-size: 18px;">✗</span>')
    tiene_constantes.short_description = 'Constantes'

    def cantidad_adjuntos(self, obj):
        """Muestra la cantidad de adjuntos"""
        count = obj.adjuntos.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #007bff; color: white; padding: 2px 8px; '
                'border-radius: 10px; font-size: 12px;">{}</span>',
                count
            )
        return '-'
    cantidad_adjuntos.short_description = 'Adjuntos'

    def get_queryset(self, request):
        """Optimiza las consultas"""
        return super().get_queryset(request).select_related(
            'mascota',
            'medico',
            'cita'
        ).prefetch_related('constantes_vitales', 'adjuntos')


@admin.register(ConstantesVitales)
class ConstantesVitalesAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para Constantes Vitales
    """

    list_display = (
        'id',
        'episodio',
        'peso',
        'temperatura',
        'frecuencia_cardiaca',
        'frecuencia_respiratoria',
        'condicion_corporal',
        'fecha_registro'
    )

    list_filter = ('fecha_registro',)

    search_fields = (
        'episodio__mascota__nombre',
        'episodio__id'
    )

    ordering = ('-fecha_registro',)

    fieldsets = (
        ('Episodio', {
            'fields': ('episodio',)
        }),
        ('Mediciones Básicas', {
            'fields': ('peso', 'temperatura', 'condicion_corporal')
        }),
        ('Frecuencias', {
            'fields': ('frecuencia_cardiaca', 'frecuencia_respiratoria')
        }),
        ('Presión Arterial', {
            'fields': ('presion_arterial_sistolica', 'presion_arterial_diastolica')
        }),
        ('Otros Parámetros', {
            'fields': ('tiempo_llenado_capilar', 'observaciones')
        }),
        ('Auditoría', {
            'fields': ('registrado_por', 'fecha_registro'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('fecha_registro',)


@admin.register(Adjunto)
class AdjuntoAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para Adjuntos
    """

    list_display = (
        'titulo',
        'tipo_badge',
        'episodio_link',
        'archivo_link',
        'fecha_subida',
        'subido_por'
    )

    list_filter = ('tipo', 'fecha_subida')

    search_fields = (
        'titulo',
        'descripcion',
        'episodio__mascota__nombre',
        'episodio__id'
    )

    ordering = ('-fecha_subida',)

    fieldsets = (
        ('Información del Adjunto', {
            'fields': ('episodio', 'tipo', 'titulo', 'descripcion', 'archivo')
        }),
        ('Auditoría', {
            'fields': ('subido_por', 'fecha_subida'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('fecha_subida',)

    def tipo_badge(self, obj):
        """Muestra el tipo con un badge de color"""
        colors = {
            'RADIOGRAFIA': '#007bff',
            'ECOGRAFIA': '#17a2b8',
            'LABORATORIO': '#28a745',
            'FOTO': '#ffc107',
            'DOCUMENTO': '#6c757d',
            'OTRO': '#6610f2',
        }
        color = colors.get(obj.tipo, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_tipo_display()
        )
    tipo_badge.short_description = 'Tipo'

    def episodio_link(self, obj):
        """Muestra el enlace al episodio"""
        return format_html(
            '<a href="/admin/hce/episodioclinico/{}/change/">Episodio #{}</a>',
            obj.episodio.id,
            obj.episodio.id
        )
    episodio_link.short_description = 'Episodio'

    def archivo_link(self, obj):
        """Muestra el enlace al archivo"""
        return format_html(
            '<a href="{}" target="_blank">Ver archivo</a>',
            obj.archivo.url
        )
    archivo_link.short_description = 'Archivo'
