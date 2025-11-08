"""
Modelos de la aplicación Citas
Maneja la gestión de citas veterinarias del sistema RamboPet
"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta


class Cita(models.Model):
    """
    Modelo principal para las citas veterinarias
    """

    class Estado(models.TextChoices):
        RESERVADA = 'RESERVADA', 'Reservada'
        CONFIRMADA = 'CONFIRMADA', 'Confirmada'
        EN_CURSO = 'EN_CURSO', 'En Curso'
        ATENDIDA = 'ATENDIDA', 'Atendida'
        CANCELADA = 'CANCELADA', 'Cancelada'
        NO_ASISTIO = 'NO_ASISTIO', 'No Asistió'

    class TipoCita(models.TextChoices):
        CONSULTA_GENERAL = 'CONSULTA_GENERAL', 'Consulta General'
        VACUNACION = 'VACUNACION', 'Vacunación'
        CIRUGIA = 'CIRUGIA', 'Cirugía'
        EMERGENCIA = 'EMERGENCIA', 'Emergencia'
        CONTROL = 'CONTROL', 'Control'
        DESPARASITACION = 'DESPARASITACION', 'Desparasitación'
        OTRO = 'OTRO', 'Otro'

    # Relaciones principales
    mascota = models.ForeignKey(
        'pacientes.Mascota',
        on_delete=models.PROTECT,
        related_name='citas',
        verbose_name='Mascota'
    )

    tutor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='citas_como_tutor',
        limit_choices_to={'rol': 'TUTOR'},
        verbose_name='Tutor'
    )

    medico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='citas_como_medico',
        limit_choices_to={'rol': 'MEDICO'},
        verbose_name='Médico Veterinario',
        null=True,
        blank=True
    )

    # Información de la cita
    fecha_hora = models.DateTimeField(
        verbose_name='Fecha y Hora de la Cita'
    )

    duracion_estimada = models.PositiveIntegerField(
        default=30,
        verbose_name='Duración Estimada (minutos)',
        help_text='Duración estimada de la cita en minutos'
    )

    tipo_cita = models.CharField(
        max_length=30,
        choices=TipoCita.choices,
        default=TipoCita.CONSULTA_GENERAL,
        verbose_name='Tipo de Cita'
    )

    estado = models.CharField(
        max_length=15,
        choices=Estado.choices,
        default=Estado.RESERVADA,
        verbose_name='Estado'
    )

    # Detalles de la cita
    motivo = models.TextField(
        verbose_name='Motivo de la Consulta',
        help_text='Descripción breve del motivo de la cita'
    )

    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones',
        help_text='Observaciones adicionales para la cita'
    )

    notas_internas = models.TextField(
        blank=True,
        verbose_name='Notas Internas',
        help_text='Notas visibles solo para el personal'
    )

    # Recordatorios y notificaciones
    recordatorio_enviado = models.BooleanField(
        default=False,
        verbose_name='Recordatorio Enviado'
    )

    fecha_recordatorio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Recordatorio'
    )

    # Fechas de cambios de estado
    fecha_confirmacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Confirmación'
    )

    fecha_atencion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Atención'
    )

    fecha_cancelacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Cancelación'
    )

    motivo_cancelacion = models.TextField(
        blank=True,
        verbose_name='Motivo de Cancelación'
    )

    # Campos de auditoría
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='citas_creadas',
        verbose_name='Creado por'
    )

    class Meta:
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['fecha_hora']
        indexes = [
            models.Index(fields=['fecha_hora', 'estado']),
            models.Index(fields=['mascota', 'estado']),
            models.Index(fields=['medico', 'fecha_hora']),
            models.Index(fields=['tutor', 'fecha_hora']),
        ]

    def __str__(self):
        return f"Cita {self.id} - {self.mascota.nombre} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"

    def clean(self):
        """Validaciones personalizadas"""
        # No permitir citas en el pasado (excepto si ya existe)
        if not self.pk and self.fecha_hora < datetime.now():
            raise ValidationError('No se pueden crear citas en el pasado')

        # Validar que el tutor de la cita sea el tutor de la mascota
        if self.tutor != self.mascota.tutor:
            raise ValidationError('El tutor de la cita debe ser el tutor de la mascota')

        # Validar que el médico tenga el rol correcto
        if self.medico and not self.medico.es_medico:
            raise ValidationError('El usuario asignado como médico debe tener el rol de médico')

    def save(self, *args, **kwargs):
        """Lógica personalizada al guardar"""
        self.full_clean()

        # Establecer el tutor automáticamente si no está definido
        if not self.tutor:
            self.tutor = self.mascota.tutor

        super().save(*args, **kwargs)

    @property
    def hora_fin_estimada(self):
        """Calcula la hora de finalización estimada de la cita"""
        return self.fecha_hora + timedelta(minutes=self.duracion_estimada)

    @property
    def esta_vencida(self):
        """Verifica si la cita ya pasó y no fue atendida"""
        return (
            self.fecha_hora < datetime.now() and
            self.estado not in [self.Estado.ATENDIDA, self.Estado.CANCELADA, self.Estado.NO_ASISTIO]
        )

    @property
    def puede_cancelarse(self):
        """Verifica si la cita puede ser cancelada"""
        return self.estado in [self.Estado.RESERVADA, self.Estado.CONFIRMADA]

    def confirmar(self):
        """Confirma la cita"""
        if self.estado == self.Estado.RESERVADA:
            self.estado = self.Estado.CONFIRMADA
            self.fecha_confirmacion = datetime.now()
            self.save()

    def iniciar_atencion(self):
        """Marca la cita como en curso"""
        if self.estado in [self.Estado.RESERVADA, self.Estado.CONFIRMADA]:
            self.estado = self.Estado.EN_CURSO
            self.save()

    def completar(self):
        """Marca la cita como atendida"""
        if self.estado == self.Estado.EN_CURSO:
            self.estado = self.Estado.ATENDIDA
            self.fecha_atencion = datetime.now()
            self.save()

    def cancelar(self, motivo=''):
        """Cancela la cita"""
        if self.puede_cancelarse:
            self.estado = self.Estado.CANCELADA
            self.fecha_cancelacion = datetime.now()
            self.motivo_cancelacion = motivo
            self.save()

    def marcar_no_asistio(self):
        """Marca la cita como no asistida"""
        if self.estado in [self.Estado.RESERVADA, self.Estado.CONFIRMADA]:
            self.estado = self.Estado.NO_ASISTIO
            self.save()
