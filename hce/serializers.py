"""
Serializers para la aplicación HCE
"""

from rest_framework import serializers
from .models import EpisodioClinico, ConstantesVitales, Adjunto
from citas.serializers import CitaListSerializer


class ConstantesVitalesSerializer(serializers.ModelSerializer):
    """
    Serializer para Constantes Vitales
    """
    registrado_por_nombre = serializers.CharField(
        source='registrado_por.get_full_name',
        read_only=True
    )

    class Meta:
        model = ConstantesVitales
        fields = [
            'id',
            'episodio',
            'peso',
            'temperatura',
            'frecuencia_cardiaca',
            'frecuencia_respiratoria',
            'presion_arterial_sistolica',
            'presion_arterial_diastolica',
            'tiempo_llenado_capilar',
            'condicion_corporal',
            'observaciones',
            'fecha_registro',
            'registrado_por',
            'registrado_por_nombre'
        ]
        read_only_fields = ['id', 'fecha_registro']


class AdjuntoSerializer(serializers.ModelSerializer):
    """
    Serializer para Adjuntos
    """
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    subido_por_nombre = serializers.CharField(
        source='subido_por.get_full_name',
        read_only=True
    )

    class Meta:
        model = Adjunto
        fields = [
            'id',
            'episodio',
            'tipo',
            'tipo_display',
            'archivo',
            'titulo',
            'descripcion',
            'fecha_subida',
            'subido_por',
            'subido_por_nombre'
        ]
        read_only_fields = ['id', 'fecha_subida']


class EpisodioClinicoSerializer(serializers.ModelSerializer):
    """
    Serializer completo para Episodio Clínico
    """
    # Campos de solo lectura con información relacionada
    mascota_nombre = serializers.CharField(source='mascota.nombre', read_only=True)
    medico_nombre = serializers.CharField(source='medico.get_full_name', read_only=True)
    pronostico_display = serializers.CharField(source='get_pronostico_display', read_only=True)

    # Relaciones incluidas
    constantes_vitales = ConstantesVitalesSerializer(many=True, read_only=True)
    adjuntos = AdjuntoSerializer(many=True, read_only=True)

    class Meta:
        model = EpisodioClinico
        fields = [
            'id',
            'cita',
            'mascota',
            'mascota_nombre',
            'medico',
            'medico_nombre',
            'motivo_consulta',
            'anamnesis',
            'examen_fisico',
            'diagnostico_presuntivo',
            'diagnostico_definitivo',
            'plan_tratamiento',
            'medicamentos',
            'procedimientos',
            'pronostico',
            'pronostico_display',
            'indicaciones',
            'proxima_revision',
            'episodio_cerrado',
            'constantes_vitales',
            'adjuntos',
            'fecha_creacion',
            'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']

    def validate_cita(self, value):
        """Valida que la cita no tenga ya un episodio clínico"""
        # Solo validar para nuevos episodios
        if not self.instance and hasattr(value, 'episodio_clinico'):
            raise serializers.ValidationError(
                "Esta cita ya tiene un episodio clínico asociado"
            )
        return value


class EpisodioClinicoListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listados de episodios clínicos
    """
    mascota_nombre = serializers.CharField(source='mascota.nombre', read_only=True)
    medico_nombre = serializers.CharField(source='medico.get_full_name', read_only=True)
    diagnostico = serializers.SerializerMethodField()
    pronostico_display = serializers.CharField(source='get_pronostico_display', read_only=True)

    class Meta:
        model = EpisodioClinico
        fields = [
            'id',
            'fecha_creacion',
            'mascota_nombre',
            'medico_nombre',
            'motivo_consulta',
            'diagnostico',
            'pronostico',
            'pronostico_display',
            'episodio_cerrado'
        ]

    def get_diagnostico(self, obj):
        """Retorna el diagnóstico definitivo o presuntivo"""
        return obj.diagnostico_definitivo or obj.diagnostico_presuntivo


class EpisodioClinicoDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para ver un episodio clínico específico
    Incluye información completa de cita, constantes y adjuntos
    """
    cita = CitaListSerializer(read_only=True)
    mascota_nombre = serializers.CharField(source='mascota.nombre', read_only=True)
    medico_nombre = serializers.CharField(source='medico.get_full_name', read_only=True)
    pronostico_display = serializers.CharField(source='get_pronostico_display', read_only=True)
    constantes_vitales = ConstantesVitalesSerializer(many=True, read_only=True)
    adjuntos = AdjuntoSerializer(many=True, read_only=True)

    class Meta:
        model = EpisodioClinico
        fields = [
            'id',
            'cita',
            'mascota',
            'mascota_nombre',
            'medico',
            'medico_nombre',
            'motivo_consulta',
            'anamnesis',
            'examen_fisico',
            'diagnostico_presuntivo',
            'diagnostico_definitivo',
            'plan_tratamiento',
            'medicamentos',
            'procedimientos',
            'pronostico',
            'pronostico_display',
            'indicaciones',
            'proxima_revision',
            'episodio_cerrado',
            'constantes_vitales',
            'adjuntos',
            'fecha_creacion',
            'fecha_actualizacion'
        ]
