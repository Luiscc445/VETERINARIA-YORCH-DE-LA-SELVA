"""
Modelos de la aplicación Usuarios
Maneja la autenticación y roles de usuarios del sistema RamboPet
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class User(AbstractUser):
    """
    Modelo de usuario personalizado que extiende AbstractUser
    Incluye campos adicionales para la gestión de la clínica veterinaria
    """

    class Rol(models.TextChoices):
        TUTOR = 'TUTOR', 'Tutor de Mascota'
        MEDICO = 'MEDICO', 'Médico Veterinario'
        RECEPCION = 'RECEPCION', 'Recepcionista'
        ADMIN = 'ADMIN', 'Administrador'

    # Campo de rol para determinar el tipo de usuario
    rol = models.CharField(
        max_length=10,
        choices=Rol.choices,
        default=Rol.TUTOR,
        verbose_name='Rol'
    )

    # Información de contacto adicional
    telefono_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="El número de teléfono debe estar en formato: '+999999999'. Hasta 15 dígitos permitidos."
    )
    telefono = models.CharField(
        validators=[telefono_regex],
        max_length=17,
        blank=True,
        verbose_name='Teléfono'
    )

    direccion = models.TextField(
        blank=True,
        verbose_name='Dirección'
    )

    fecha_nacimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Nacimiento'
    )

    # Campos específicos para médicos veterinarios
    cedula_profesional = models.CharField(
        max_length=50,
        blank=True,
        unique=True,
        null=True,
        verbose_name='Cédula Profesional'
    )

    especialidad = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Especialidad'
    )

    # Información adicional
    foto_perfil = models.ImageField(
        upload_to='usuarios/perfiles/',
        null=True,
        blank=True,
        verbose_name='Foto de Perfil'
    )

    activo = models.BooleanField(
        default=True,
        verbose_name='Usuario Activo'
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
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-fecha_registro']
        indexes = [
            models.Index(fields=['rol', 'activo']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"

    def save(self, *args, **kwargs):
        # Validación: Solo médicos pueden tener cédula profesional y especialidad
        if self.rol != self.Rol.MEDICO:
            self.cedula_profesional = None
            self.especialidad = ''
        super().save(*args, **kwargs)

    @property
    def es_medico(self):
        """Retorna True si el usuario es médico"""
        return self.rol == self.Rol.MEDICO

    @property
    def es_tutor(self):
        """Retorna True si el usuario es tutor"""
        return self.rol == self.Rol.TUTOR

    @property
    def es_personal(self):
        """Retorna True si el usuario es personal (médico, recepción o admin)"""
        return self.rol in [self.Rol.MEDICO, self.Rol.RECEPCION, self.Rol.ADMIN]
