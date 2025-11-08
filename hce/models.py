"""
Modelos de la aplicación HCE (Historia Clínica Electrónica)
Maneja los episodios clínicos, constantes vitales y adjuntos médicos
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class EpisodioClinico(models.Model):
    """
    Modelo para los episodios clínicos
    Cada episodio está relacionado con una cita y documenta la atención médica
    """

    # Relación con la cita
    cita = models.OneToOneField(
        'citas.Cita',
        on_delete=models.PROTECT,
        related_name='episodio_clinico',
        verbose_name='Cita Asociada'
    )

    # Información del episodio
    mascota = models.ForeignKey(
        'pacientes.Mascota',
        on_delete=models.PROTECT,
        related_name='episodios_clinicos',
        verbose_name='Mascota'
    )

    medico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='episodios_atendidos',
        limit_choices_to={'rol': 'MEDICO'},
        verbose_name='Médico Tratante'
    )

    # Motivo de consulta y anamnesis
    motivo_consulta = models.TextField(
        verbose_name='Motivo de Consulta',
        help_text='Razón principal por la que se consulta'
    )

    anamnesis = models.TextField(
        verbose_name='Anamnesis',
        help_text='Historia clínica y antecedentes relevantes del episodio'
    )

    # Examen físico
    examen_fisico = models.TextField(
        verbose_name='Examen Físico',
        help_text='Hallazgos del examen físico general'
    )

    # Diagnóstico
    diagnostico_presuntivo = models.TextField(
        verbose_name='Diagnóstico Presuntivo',
        help_text='Diagnóstico inicial basado en examen clínico'
    )

    diagnostico_definitivo = models.TextField(
        blank=True,
        verbose_name='Diagnóstico Definitivo',
        help_text='Diagnóstico confirmado con pruebas complementarias'
    )

    # Tratamiento y plan
    plan_tratamiento = models.TextField(
        verbose_name='Plan de Tratamiento',
        help_text='Descripción del tratamiento prescrito'
    )

    medicamentos = models.TextField(
        blank=True,
        verbose_name='Medicamentos Prescritos',
        help_text='Lista de medicamentos con dosis y duración'
    )

    procedimientos = models.TextField(
        blank=True,
        verbose_name='Procedimientos Realizados',
        help_text='Descripción de procedimientos o intervenciones realizadas'
    )

    # Pronóstico y seguimiento
    pronostico = models.CharField(
        max_length=20,
        choices=[
            ('EXCELENTE', 'Excelente'),
            ('BUENO', 'Bueno'),
            ('RESERVADO', 'Reservado'),
            ('GRAVE', 'Grave'),
        ],
        default='BUENO',
        verbose_name='Pronóstico'
    )

    indicaciones = models.TextField(
        blank=True,
        verbose_name='Indicaciones al Tutor',
        help_text='Instrucciones para el cuidado en casa'
    )

    proxima_revision = models.DateField(
        null=True,
        blank=True,
        verbose_name='Próxima Revisión',
        help_text='Fecha recomendada para próxima consulta'
    )

    # Estado del episodio
    episodio_cerrado = models.BooleanField(
        default=False,
        verbose_name='Episodio Cerrado',
        help_text='Indica si el episodio clínico fue finalizado'
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

    class Meta:
        verbose_name = 'Episodio Clínico'
        verbose_name_plural = 'Episodios Clínicos'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['mascota', '-fecha_creacion']),
            models.Index(fields=['medico', '-fecha_creacion']),
            models.Index(fields=['cita']),
        ]

    def __str__(self):
        return f"Episodio {self.id} - {self.mascota.nombre} - {self.fecha_creacion.strftime('%d/%m/%Y')}"

    def save(self, *args, **kwargs):
        """Establece valores por defecto desde la cita"""
        if not self.mascota_id:
            self.mascota = self.cita.mascota

        if not self.medico_id and self.cita.medico:
            self.medico = self.cita.medico

        if not self.motivo_consulta:
            self.motivo_consulta = self.cita.motivo

        super().save(*args, **kwargs)


class ConstantesVitales(models.Model):
    """
    Modelo para las constantes vitales registradas en un episodio clínico
    """

    episodio = models.ForeignKey(
        EpisodioClinico,
        on_delete=models.CASCADE,
        related_name='constantes_vitales',
        verbose_name='Episodio Clínico'
    )

    # Peso y temperatura
    peso = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name='Peso (kg)',
        help_text='Peso en kilogramos'
    )

    temperatura = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(30.0), MaxValueValidator(45.0)],
        verbose_name='Temperatura (°C)',
        help_text='Temperatura corporal en grados Celsius'
    )

    # Frecuencias
    frecuencia_cardiaca = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(10), MaxValueValidator(300)],
        verbose_name='Frecuencia Cardíaca (lpm)',
        help_text='Latidos por minuto'
    )

    frecuencia_respiratoria = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(5), MaxValueValidator(100)],
        verbose_name='Frecuencia Respiratoria (rpm)',
        help_text='Respiraciones por minuto'
    )

    # Otros parámetros
    presion_arterial_sistolica = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Presión Arterial Sistólica (mmHg)'
    )

    presion_arterial_diastolica = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Presión Arterial Diastólica (mmHg)'
    )

    tiempo_llenado_capilar = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.1), MaxValueValidator(10.0)],
        verbose_name='Tiempo de Llenado Capilar (seg)',
        help_text='Tiempo en segundos'
    )

    condicion_corporal = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(9)],
        verbose_name='Condición Corporal',
        help_text='Escala de 1 a 9 (1: muy delgado, 5: ideal, 9: obeso)'
    )

    # Observaciones
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones',
        help_text='Observaciones adicionales sobre las constantes vitales'
    )

    # Auditoría
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Registro'
    )

    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Registrado por'
    )

    class Meta:
        verbose_name = 'Constantes Vitales'
        verbose_name_plural = 'Constantes Vitales'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"Constantes - {self.episodio.mascota.nombre} - {self.fecha_registro.strftime('%d/%m/%Y %H:%M')}"


class Adjunto(models.Model):
    """
    Modelo para adjuntar archivos a un episodio clínico
    (Radiografías, análisis de laboratorio, imágenes, etc.)
    """

    class TipoAdjunto(models.TextChoices):
        RADIOGRAFIA = 'RADIOGRAFIA', 'Radiografía'
        ECOGRAFIA = 'ECOGRAFIA', 'Ecografía'
        LABORATORIO = 'LABORATORIO', 'Análisis de Laboratorio'
        FOTO = 'FOTO', 'Fotografía'
        DOCUMENTO = 'DOCUMENTO', 'Documento'
        OTRO = 'OTRO', 'Otro'

    episodio = models.ForeignKey(
        EpisodioClinico,
        on_delete=models.CASCADE,
        related_name='adjuntos',
        verbose_name='Episodio Clínico'
    )

    tipo = models.CharField(
        max_length=20,
        choices=TipoAdjunto.choices,
        default=TipoAdjunto.DOCUMENTO,
        verbose_name='Tipo de Adjunto'
    )

    archivo = models.FileField(
        upload_to='hce/adjuntos/%Y/%m/',
        verbose_name='Archivo'
    )

    titulo = models.CharField(
        max_length=200,
        verbose_name='Título',
        help_text='Título descriptivo del archivo'
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )

    # Auditoría
    fecha_subida = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Subida'
    )

    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Subido por'
    )

    class Meta:
        verbose_name = 'Adjunto'
        verbose_name_plural = 'Adjuntos'
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"{self.titulo} - {self.get_tipo_display()}"
