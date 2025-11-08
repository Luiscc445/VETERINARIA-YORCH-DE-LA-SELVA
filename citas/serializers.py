"""
Serializers para la aplicación Citas
"""

from rest_framework import serializers
from datetime import datetime, timedelta
from .models import Cita
from pacientes.serializers import MascotaListSerializer
from usuarios.serializers import MedicoSerializer, TutorSerializer


class CitaSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo Cita
    """
    # Campos de solo lectura con información relacionada
    mascota_nombre = serializers.CharField(source='mascota.nombre', read_only=True)
    tutor_nombre = serializers.CharField(source='tutor.get_full_name', read_only=True)
    medico_nombre = serializers.CharField(source='medico.get_full_name', read_only=True)
    tipo_cita_display = serializers.CharField(source='get_tipo_cita_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    hora_fin_estimada = serializers.DateTimeField(read_only=True)
    esta_vencida = serializers.BooleanField(read_only=True)
    puede_cancelarse = serializers.BooleanField(read_only=True)

    class Meta:
        model = Cita
        fields = [
            'id',
            'mascota',
            'mascota_nombre',
            'tutor',
            'tutor_nombre',
            'medico',
            'medico_nombre',
            'fecha_hora',
            'duracion_estimada',
            'hora_fin_estimada',
            'tipo_cita',
            'tipo_cita_display',
            'estado',
            'estado_display',
            'motivo',
            'observaciones',
            'notas_internas',
            'recordatorio_enviado',
            'fecha_recordatorio',
            'fecha_confirmacion',
            'fecha_atencion',
            'fecha_cancelacion',
            'motivo_cancelacion',
            'esta_vencida',
            'puede_cancelarse',
            'fecha_creacion',
            'fecha_actualizacion',
            'creado_por'
        ]
        read_only_fields = [
            'id',
            'fecha_confirmacion',
            'fecha_atencion',
            'fecha_cancelacion',
            'fecha_creacion',
            'fecha_actualizacion',
            'recordatorio_enviado',
            'fecha_recordatorio'
        ]

    def validate_fecha_hora(self, value):
        """Valida que la fecha de la cita sea futura"""
        # Solo validar para nuevas citas
        if not self.instance and value < datetime.now():
            raise serializers.ValidationError(
                "No se pueden crear citas en el pasado"
            )
        return value

    def validate(self, attrs):
        """Validaciones personalizadas"""
        # Validar que el tutor de la cita sea el tutor de la mascota
        mascota = attrs.get('mascota', getattr(self.instance, 'mascota', None))
        tutor = attrs.get('tutor', getattr(self.instance, 'tutor', None))

        if mascota and tutor and tutor != mascota.tutor:
            raise serializers.ValidationError({
                'tutor': 'El tutor de la cita debe ser el tutor de la mascota'
            })

        # Validar que el médico tenga el rol correcto
        medico = attrs.get('medico')
        if medico and not medico.es_medico:
            raise serializers.ValidationError({
                'medico': 'El usuario asignado debe tener el rol de médico'
            })

        return attrs


class CitaListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listados de citas
    """
    mascota_nombre = serializers.CharField(source='mascota.nombre', read_only=True)
    tutor_nombre = serializers.CharField(source='tutor.get_full_name', read_only=True)
    medico_nombre = serializers.CharField(source='medico.get_full_name', read_only=True)
    tipo_cita_display = serializers.CharField(source='get_tipo_cita_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Cita
        fields = [
            'id',
            'fecha_hora',
            'duracion_estimada',
            'mascota_nombre',
            'tutor_nombre',
            'medico_nombre',
            'tipo_cita',
            'tipo_cita_display',
            'estado',
            'estado_display',
            'motivo'
        ]


class CitaDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para ver una cita específica
    Incluye información completa de mascota, tutor y médico
    """
    mascota = MascotaListSerializer(read_only=True)
    tutor = TutorSerializer(read_only=True)
    medico = MedicoSerializer(read_only=True)
    tipo_cita_display = serializers.CharField(source='get_tipo_cita_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    hora_fin_estimada = serializers.DateTimeField(read_only=True)
    esta_vencida = serializers.BooleanField(read_only=True)
    puede_cancelarse = serializers.BooleanField(read_only=True)

    class Meta:
        model = Cita
        fields = [
            'id',
            'mascota',
            'tutor',
            'medico',
            'fecha_hora',
            'duracion_estimada',
            'hora_fin_estimada',
            'tipo_cita',
            'tipo_cita_display',
            'estado',
            'estado_display',
            'motivo',
            'observaciones',
            'notas_internas',
            'recordatorio_enviado',
            'fecha_recordatorio',
            'fecha_confirmacion',
            'fecha_atencion',
            'fecha_cancelacion',
            'motivo_cancelacion',
            'esta_vencida',
            'puede_cancelarse',
            'fecha_creacion',
            'fecha_actualizacion'
        ]


class CitaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer específico para crear citas
    """
    class Meta:
        model = Cita
        fields = [
            'mascota',
            'tutor',
            'medico',
            'fecha_hora',
            'duracion_estimada',
            'tipo_cita',
            'motivo',
            'observaciones'
        ]

    def validate_fecha_hora(self, value):
        """Valida que la fecha de la cita sea futura"""
        if value < datetime.now():
            raise serializers.ValidationError(
                "No se pueden crear citas en el pasado"
            )
        return value

    def validate(self, attrs):
        """Validaciones personalizadas"""
        mascota = attrs.get('mascota')
        tutor = attrs.get('tutor')

        # Establecer el tutor automáticamente si no se proporciona
        if not tutor and mascota:
            attrs['tutor'] = mascota.tutor

        # Validar que el tutor sea el tutor de la mascota
        if tutor and tutor != mascota.tutor:
            raise serializers.ValidationError({
                'tutor': 'El tutor de la cita debe ser el tutor de la mascota'
            })

        return attrs
