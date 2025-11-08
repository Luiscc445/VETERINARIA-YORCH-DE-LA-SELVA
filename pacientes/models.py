"""
Modelos de la aplicación Pacientes
Maneja las mascotas, especies y razas del sistema RamboPet
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class Especie(models.Model):
    """
    Modelo para las especies de animales
    Ej: Perro, Gato, Ave, Reptil, etc.
    """

    nombre = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Nombre de Especie'
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )

    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )

    # Campos de auditoría
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )

    class Meta:
        verbose_name = 'Especie'
        verbose_name_plural = 'Especies'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Raza(models.Model):
    """
    Modelo para las razas de animales
    Cada raza pertenece a una especie
    """

    especie = models.ForeignKey(
        Especie,
        on_delete=models.CASCADE,
        related_name='razas',
        verbose_name='Especie'
    )

    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre de Raza'
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )

    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )

    # Campos de auditoría
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )

    class Meta:
        verbose_name = 'Raza'
        verbose_name_plural = 'Razas'
        ordering = ['especie', 'nombre']
        unique_together = ['especie', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.especie.nombre})"


class Mascota(models.Model):
    """
    Modelo principal para las mascotas (pacientes veterinarios)
    """

    class Sexo(models.TextChoices):
        MACHO = 'M', 'Macho'
        HEMBRA = 'H', 'Hembra'
        DESCONOCIDO = 'D', 'Desconocido'

    # Relación con el tutor
    tutor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='mascotas',
        limit_choices_to={'rol': 'TUTOR'},
        verbose_name='Tutor'
    )

    # Información básica
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre'
    )

    especie = models.ForeignKey(
        Especie,
        on_delete=models.PROTECT,
        related_name='mascotas',
        verbose_name='Especie'
    )

    raza = models.ForeignKey(
        Raza,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mascotas',
        verbose_name='Raza'
    )

    sexo = models.CharField(
        max_length=1,
        choices=Sexo.choices,
        default=Sexo.DESCONOCIDO,
        verbose_name='Sexo'
    )

    fecha_nacimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Nacimiento'
    )

    # Características físicas
    color = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Color/Patrón'
    )

    peso_actual = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01)],
        verbose_name='Peso Actual (kg)',
        help_text='Peso en kilogramos'
    )

    # Identificación
    microchip = models.CharField(
        max_length=50,
        blank=True,
        unique=True,
        null=True,
        verbose_name='Número de Microchip'
    )

    foto = models.ImageField(
        upload_to='pacientes/fotos/',
        null=True,
        blank=True,
        verbose_name='Foto de la Mascota'
    )

    # Información médica básica
    esterilizado = models.BooleanField(
        default=False,
        verbose_name='Esterilizado/Castrado'
    )

    alergias = models.TextField(
        blank=True,
        verbose_name='Alergias Conocidas'
    )

    condiciones_cronicas = models.TextField(
        blank=True,
        verbose_name='Condiciones Crónicas'
    )

    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones Generales'
    )

    # Estado
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Indica si la mascota está activa en el sistema'
    )

    fallecido = models.BooleanField(
        default=False,
        verbose_name='Fallecido'
    )

    fecha_fallecimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Fallecimiento'
    )

    # Campos de auditoría
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Registro'
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )

    class Meta:
        verbose_name = 'Mascota'
        verbose_name_plural = 'Mascotas'
        ordering = ['-fecha_registro']
        indexes = [
            models.Index(fields=['tutor', 'activo']),
            models.Index(fields=['especie']),
            models.Index(fields=['microchip']),
        ]

    def __str__(self):
        return f"{self.nombre} - {self.especie.nombre} ({self.tutor.get_full_name()})"

    @property
    def edad_aproximada(self):
        """Calcula la edad aproximada en años"""
        if not self.fecha_nacimiento:
            return None

        from datetime import date
        today = date.today()
        edad = today.year - self.fecha_nacimiento.year

        # Ajustar si aún no ha cumplido años este año
        if today.month < self.fecha_nacimiento.month or \
           (today.month == self.fecha_nacimiento.month and today.day < self.fecha_nacimiento.day):
            edad -= 1

        return edad

    def save(self, *args, **kwargs):
        """Validaciones personalizadas al guardar"""
        # Si está fallecido, marcar como inactivo
        if self.fallecido:
            self.activo = False

        # Validar que la raza pertenezca a la especie
        if self.raza and self.raza.especie != self.especie:
            raise ValueError(
                f"La raza {self.raza.nombre} no pertenece a la especie {self.especie.nombre}"
            )

        super().save(*args, **kwargs)
