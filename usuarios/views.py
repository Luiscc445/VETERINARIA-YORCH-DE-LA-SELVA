"""
Views para la aplicación Usuarios
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import User
from .serializers import (
    UserSerializer,
    UserListSerializer,
    MedicoSerializer,
    TutorSerializer,
    UserProfileSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión completa de usuarios

    Endpoints:
    - GET /api/v1/usuarios/ - Lista todos los usuarios
    - POST /api/v1/usuarios/ - Crea un nuevo usuario
    - GET /api/v1/usuarios/{id}/ - Obtiene un usuario específico
    - PUT /api/v1/usuarios/{id}/ - Actualiza un usuario
    - PATCH /api/v1/usuarios/{id}/ - Actualización parcial
    - DELETE /api/v1/usuarios/{id}/ - Elimina un usuario
    - GET /api/v1/usuarios/medicos/ - Lista solo médicos
    - GET /api/v1/usuarios/tutores/ - Lista solo tutores
    - GET /api/v1/usuarios/profile/ - Obtiene el perfil del usuario actual
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # Campos para filtrado
    filterset_fields = ['rol', 'is_active', 'activo']

    # Campos para búsqueda
    search_fields = [
        'username',
        'first_name',
        'last_name',
        'email',
        'telefono',
        'cedula_profesional'
    ]

    # Campos para ordenamiento
    ordering_fields = ['fecha_registro', 'username', 'first_name', 'last_name']
    ordering = ['-fecha_registro']

    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'profile':
            return UserProfileSerializer
        return UserSerializer

    def get_permissions(self):
        """
        Permisos personalizados por acción
        Permite registro público, pero requiere autenticación para otras acciones
        """
        if self.action == 'create':
            # Permitir creación pública (registro de tutores)
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def medicos(self, request):
        """
        Endpoint personalizado para listar solo médicos veterinarios
        GET /api/v1/usuarios/medicos/
        """
        medicos = self.queryset.filter(rol=User.Rol.MEDICO, activo=True)
        serializer = MedicoSerializer(medicos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def tutores(self, request):
        """
        Endpoint personalizado para listar solo tutores
        GET /api/v1/usuarios/tutores/
        """
        tutores = self.queryset.filter(rol=User.Rol.TUTOR, activo=True)
        serializer = TutorSerializer(tutores, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get', 'put', 'patch'])
    def profile(self, request):
        """
        Endpoint para obtener/actualizar el perfil del usuario actual
        GET /api/v1/usuarios/profile/
        PUT /api/v1/usuarios/profile/
        PATCH /api/v1/usuarios/profile/
        """
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)

        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = self.get_serializer(
                request.user,
                data=request.data,
                partial=partial
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activa un usuario
        POST /api/v1/usuarios/{id}/activate/
        """
        user = self.get_object()
        user.activo = True
        user.is_active = True
        user.save()
        return Response(
            {'status': 'Usuario activado exitosamente'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Desactiva un usuario
        POST /api/v1/usuarios/{id}/deactivate/
        """
        user = self.get_object()
        user.activo = False
        user.is_active = False
        user.save()
        return Response(
            {'status': 'Usuario desactivado exitosamente'},
            status=status.HTTP_200_OK
        )
