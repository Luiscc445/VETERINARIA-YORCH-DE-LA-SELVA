"""
Serializers para la aplicación Usuarios
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo User
    Incluye todos los campos relevantes
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'rol',
            'telefono',
            'direccion',
            'fecha_nacimiento',
            'cedula_profesional',
            'especialidad',
            'foto_perfil',
            'activo',
            'is_active',
            'fecha_registro',
            'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'fecha_registro', 'fecha_actualizacion']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, attrs):
        """Valida que las contraseñas coincidan"""
        if 'password' in attrs and 'password_confirm' in attrs:
            if attrs['password'] != attrs['password_confirm']:
                raise serializers.ValidationError({
                    "password": "Las contraseñas no coinciden."
                })
        return attrs

    def validate_cedula_profesional(self, value):
        """Valida que la cédula profesional sea única si se proporciona"""
        if value:
            # Si estamos actualizando, excluir el usuario actual
            queryset = User.objects.filter(cedula_profesional=value)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError("Esta cédula profesional ya está registrada.")
        return value

    def create(self, validated_data):
        """Crea un nuevo usuario con contraseña encriptada"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        """Actualiza un usuario existente"""
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listados de usuarios
    """
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'nombre_completo',
            'rol',
            'telefono',
            'foto_perfil',
            'activo'
        ]

    def get_nombre_completo(self, obj):
        return obj.get_full_name()


class MedicoSerializer(serializers.ModelSerializer):
    """
    Serializer específico para médicos veterinarios
    """
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'nombre_completo',
            'email',
            'telefono',
            'cedula_profesional',
            'especialidad',
            'foto_perfil'
        ]

    def get_nombre_completo(self, obj):
        return obj.get_full_name()


class TutorSerializer(serializers.ModelSerializer):
    """
    Serializer específico para tutores
    """
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'nombre_completo',
            'email',
            'telefono',
            'direccion',
            'foto_perfil'
        ]

    def get_nombre_completo(self, obj):
        return obj.get_full_name()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil del usuario actual
    """
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'nombre_completo',
            'first_name',
            'last_name',
            'rol',
            'telefono',
            'direccion',
            'fecha_nacimiento',
            'foto_perfil',
            'cedula_profesional',
            'especialidad',
            'fecha_registro'
        ]
        read_only_fields = ['id', 'username', 'rol', 'fecha_registro']

    def get_nombre_completo(self, obj):
        return obj.get_full_name()
