"""
Configuración del Admin para la aplicación Citas
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Cita


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para Citas
    """

    list_display = (
        'id',
        'fecha_hora_formatted',
        'mascota_link',
        'tutor_link',
        'medico_link',
        'tipo_cita_badge',
        'estado_badge',
        'duracion_estimada',
        'recordatorio_enviado_icon'
    )

    list_filter = (
        'estado',
        'tipo_cita',
        'fecha_hora',
        'recordatorio_enviado',
        'medico'
    )

    search_fields = (
        'mascota__nombre',
        'tutor__first_name',
        'tutor__last_name',
        'medico__first_name',
        'medico__last_name',
        'motivo',
        'id'
    )

    ordering = ('-fecha_hora',)

    date_hierarchy = 'fecha_hora'

    fieldsets = (
        ('Información del Paciente', {
            'fields': ('mascota', 'tutor')
        }),
        ('Información de la Cita', {
            'fields': (
                'fecha_hora',
                'duracion_estimada',
                'tipo_cita',
                'medico',
                'motivo',
                'observaciones'
            )
        }),
        ('Estado y Seguimiento', {
            'fields': (
                'estado',
                'notas_internas',
                'fecha_confirmacion',
                'fecha_atencion'
            )
        }),
        ('Cancelación', {
            'fields': ('fecha_cancelacion', 'motivo_cancelacion'),
            'classes': ('collapse',)
        }),
        ('Recordatorios', {
            'fields': ('recordatorio_enviado', 'fecha_recordatorio'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = (
        'fecha_creacion',
        'fecha_actualizacion',
        'fecha_confirmacion',
        'fecha_atencion',
        'fecha_cancelacion'
    )

    autocomplete_fields = ['mascota', 'tutor', 'medico']

    def fecha_hora_formatted(self, obj):
        """Formatea la fecha y hora de la cita"""
        return obj.fecha_hora.strftime('%d/%m/%Y %H:%M')
    fecha_hora_formatted.short_description = 'Fecha y Hora'
    fecha_hora_formatted.admin_order_field = 'fecha_hora'

    def mascota_link(self, obj):
        """Muestra el nombre de la mascota con enlace"""
        return format_html(
            '<a href="/admin/pacientes/mascota/{}/change/">{}</a>',
            obj.mascota.id,
            obj.mascota.nombre
        )
    mascota_link.short_description = 'Mascota'

    def tutor_link(self, obj):
        """Muestra el nombre del tutor con enlace"""
        return format_html(
            '<a href="/admin/usuarios/user/{}/change/">{}</a>',
            obj.tutor.id,
            obj.tutor.get_full_name() or obj.tutor.username
        )
    tutor_link.short_description = 'Tutor'

    def medico_link(self, obj):
        """Muestra el nombre del médico con enlace"""
        if obj.medico:
            return format_html(
                '<a href="/admin/usuarios/user/{}/change/">{}</a>',
                obj.medico.id,
                obj.medico.get_full_name() or obj.medico.username
            )
        return '-'
    medico_link.short_description = 'Médico'

    def tipo_cita_badge(self, obj):
        """Muestra el tipo de cita con un badge de color"""
        colors = {
            'CONSULTA_GENERAL': '#17a2b8',
            'VACUNACION': '#28a745',
            'CIRUGIA': '#dc3545',
            'EMERGENCIA': '#ff4444',
            'CONTROL': '#ffc107',
            'DESPARASITACION': '#6610f2',
            'OTRO': '#6c757d',
        }
        color = colors.get(obj.tipo_cita, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_tipo_cita_display()
        )
    tipo_cita_badge.short_description = 'Tipo'

    def estado_badge(self, obj):
        """Muestra el estado con un badge de color"""
        colors = {
            'RESERVADA': '#007bff',
            'CONFIRMADA': '#17a2b8',
            'EN_CURSO': '#ffc107',
            'ATENDIDA': '#28a745',
            'CANCELADA': '#dc3545',
            'NO_ASISTIO': '#6c757d',
        }
        color = colors.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'

    def recordatorio_enviado_icon(self, obj):
        """Muestra un icono si se envió el recordatorio"""
        if obj.recordatorio_enviado:
            return format_html(
                '<span style="color: #28a745; font-size: 18px;">✓</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-size: 18px;">✗</span>'
        )
    recordatorio_enviado_icon.short_description = 'Recordatorio'

    def get_queryset(self, request):
        """Optimiza las consultas"""
        return super().get_queryset(request).select_related(
            'mascota',
            'tutor',
            'medico',
            'creado_por'
        )

    actions = ['marcar_confirmadas', 'marcar_atendidas', 'marcar_canceladas']

    def marcar_confirmadas(self, request, queryset):
        """Acción masiva para confirmar citas"""
        updated = queryset.filter(estado=Cita.Estado.RESERVADA).update(
            estado=Cita.Estado.CONFIRMADA,
            fecha_confirmacion=timezone.now()
        )
        self.message_user(request, f'{updated} cita(s) confirmada(s) exitosamente.')
    marcar_confirmadas.short_description = 'Marcar como Confirmadas'

    def marcar_atendidas(self, request, queryset):
        """Acción masiva para marcar citas como atendidas"""
        updated = queryset.filter(
            estado__in=[Cita.Estado.CONFIRMADA, Cita.Estado.EN_CURSO]
        ).update(
            estado=Cita.Estado.ATENDIDA,
            fecha_atencion=timezone.now()
        )
        self.message_user(request, f'{updated} cita(s) marcada(s) como atendidas.')
    marcar_atendidas.short_description = 'Marcar como Atendidas'

    def marcar_canceladas(self, request, queryset):
        """Acción masiva para cancelar citas"""
        updated = queryset.filter(
            estado__in=[Cita.Estado.RESERVADA, Cita.Estado.CONFIRMADA]
        ).update(
            estado=Cita.Estado.CANCELADA,
            fecha_cancelacion=timezone.now()
        )
        self.message_user(request, f'{updated} cita(s) cancelada(s).')
    marcar_canceladas.short_description = 'Marcar como Canceladas'
