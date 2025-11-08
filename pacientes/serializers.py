"""
Serializers para la aplicación Pacientes
"""

from rest_framework import serializers
from .models import Especie, Raza, Mascota
from usuarios.serializers import TutorSerializer


class EspecieSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Especie
    """
    cantidad_razas = serializers.SerializerMethodField()
    cantidad_mascotas = serializers.SerializerMethodField()

    class Meta:
        model = Especie
        fields = [
            'id',
            'nombre',
            'descripcion',
            'activo',
            'cantidad_razas',
            'cantidad_mascotas',
            'fecha_creacion'
        ]
        read_only_fields = ['id', 'fecha_creacion']

    def get_cantidad_razas(self, obj):
        return obj.razas.count()

    def get_cantidad_mascotas(self, obj):
        return obj.mascotas.count()


class RazaSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Raza
    """
    especie_nombre = serializers.CharField(source='especie.nombre', read_only=True)
    cantidad_mascotas = serializers.SerializerMethodField()

    class Meta:
        model = Raza
        fields = [
            'id',
            'especie',
            'especie_nombre',
            'nombre',
            'descripcion',
            'activo',
            'cantidad_mascotas',
            'fecha_creacion'
        ]
        read_only_fields = ['id', 'fecha_creacion']

    def get_cantidad_mascotas(self, obj):
        return obj.mascotas.count()


class MascotaSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo Mascota
    """
    # Campos de solo lectura con información relacionada
    tutor_nombre = serializers.CharField(source='tutor.get_full_name', read_only=True)
    especie_nombre = serializers.CharField(source='especie.nombre', read_only=True)
    raza_nombre = serializers.CharField(source='raza.nombre', read_only=True)
    edad_aproximada = serializers.IntegerField(read_only=True)
    sexo_display = serializers.CharField(source='get_sexo_display', read_only=True)

    class Meta:
        model = Mascota
        fields = [
            'id',
            'tutor',
            'tutor_nombre',
            'nombre',
            'especie',
            'especie_nombre',
            'raza',
            'raza_nombre',
            'sexo',
            'sexo_display',
            'fecha_nacimiento',
            'edad_aproximada',
            'color',
            'peso_actual',
            'microchip',
            'foto',
            'esterilizado',
            'alergias',
            'condiciones_cronicas',
            'observaciones',
            'activo',
            'fallecido',
            'fecha_fallecimiento',
            'fecha_registro',
            'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'fecha_registro', 'fecha_actualizacion']

    def validate(self, attrs):
        """Validaciones personalizadas"""
        # Validar que la raza pertenezca a la especie
        raza = attrs.get('raza')
        especie = attrs.get('especie')

        if raza and especie:
            if raza.especie != especie:
                raise serializers.ValidationError({
                    'raza': f'La raza {raza.nombre} no pertenece a la especie {especie.nombre}'
                })

        # Validar fecha de fallecimiento si está fallecido
        fallecido = attrs.get('fallecido', False)
        fecha_fallecimiento = attrs.get('fecha_fallecimiento')

        if fallecido and not fecha_fallecimiento:
            raise serializers.ValidationError({
                'fecha_fallecimiento': 'Debe proporcionar la fecha de fallecimiento si la mascota está fallecida'
            })

        return attrs


class MascotaListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listados de mascotas
    """
    tutor_nombre = serializers.CharField(source='tutor.get_full_name', read_only=True)
    especie_nombre = serializers.CharField(source='especie.nombre', read_only=True)
    raza_nombre = serializers.CharField(source='raza.nombre', read_only=True)
    edad_aproximada = serializers.IntegerField(read_only=True)

    class Meta:
        model = Mascota
        fields = [
            'id',
            'nombre',
            'tutor_nombre',
            'especie_nombre',
            'raza_nombre',
            'sexo',
            'edad_aproximada',
            'peso_actual',
            'foto',
            'activo',
            'fallecido'
        ]


class MascotaDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para ver una mascota específica
    Incluye información completa del tutor
    """
    tutor = TutorSerializer(read_only=True)
    especie = EspecieSerializer(read_only=True)
    raza = RazaSerializer(read_only=True)
    edad_aproximada = serializers.IntegerField(read_only=True)
    sexo_display = serializers.CharField(source='get_sexo_display', read_only=True)

    class Meta:
        model = Mascota
        fields = [
            'id',
            'tutor',
            'nombre',
            'especie',
            'raza',
            'sexo',
            'sexo_display',
            'fecha_nacimiento',
            'edad_aproximada',
            'color',
            'peso_actual',
            'microchip',
            'foto',
            'esterilizado',
            'alergias',
            'condiciones_cronicas',
            'observaciones',
            'activo',
            'fallecido',
            'fecha_fallecimiento',
            'fecha_registro',
            'fecha_actualizacion'
        ]
