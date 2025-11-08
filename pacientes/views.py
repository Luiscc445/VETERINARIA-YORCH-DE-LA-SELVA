"""
Views para la aplicación Pacientes
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Especie, Raza, Mascota
from .serializers import (
    EspecieSerializer,
    RazaSerializer,
    MascotaSerializer,
    MascotaListSerializer,
    MascotaDetailSerializer
)


class EspecieViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de especies

    Endpoints:
    - GET /api/v1/pacientes/especies/ - Lista todas las especies
    - POST /api/v1/pacientes/especies/ - Crea una nueva especie
    - GET /api/v1/pacientes/especies/{id}/ - Obtiene una especie específica
    - PUT/PATCH /api/v1/pacientes/especies/{id}/ - Actualiza una especie
    - DELETE /api/v1/pacientes/especies/{id}/ - Elimina una especie
    """

    queryset = Especie.objects.all()
    serializer_class = EspecieSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_fields = ['activo']
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'fecha_creacion']
    ordering = ['nombre']

    @action(detail=True, methods=['get'])
    def razas(self, request, pk=None):
        """
        Obtiene todas las razas de una especie específica
        GET /api/v1/pacientes/especies/{id}/razas/
        """
        especie = self.get_object()
        razas = especie.razas.filter(activo=True)
        serializer = RazaSerializer(razas, many=True)
        return Response(serializer.data)


class RazaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de razas

    Endpoints:
    - GET /api/v1/pacientes/razas/ - Lista todas las razas
    - POST /api/v1/pacientes/razas/ - Crea una nueva raza
    - GET /api/v1/pacientes/razas/{id}/ - Obtiene una raza específica
    - PUT/PATCH /api/v1/pacientes/razas/{id}/ - Actualiza una raza
    - DELETE /api/v1/pacientes/razas/{id}/ - Elimina una raza
    """

    queryset = Raza.objects.select_related('especie')
    serializer_class = RazaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_fields = ['especie', 'activo']
    search_fields = ['nombre', 'descripcion', 'especie__nombre']
    ordering_fields = ['nombre', 'especie__nombre', 'fecha_creacion']
    ordering = ['especie__nombre', 'nombre']


class MascotaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de mascotas

    Endpoints:
    - GET /api/v1/pacientes/mascotas/ - Lista todas las mascotas
    - POST /api/v1/pacientes/mascotas/ - Crea una nueva mascota
    - GET /api/v1/pacientes/mascotas/{id}/ - Obtiene una mascota específica
    - PUT/PATCH /api/v1/pacientes/mascotas/{id}/ - Actualiza una mascota
    - DELETE /api/v1/pacientes/mascotas/{id}/ - Elimina una mascota
    - GET /api/v1/pacientes/mascotas/mis-mascotas/ - Obtiene las mascotas del usuario actual
    """

    queryset = Mascota.objects.select_related('tutor', 'especie', 'raza')
    serializer_class = MascotaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # Campos para filtrado
    filterset_fields = [
        'tutor',
        'especie',
        'raza',
        'sexo',
        'esterilizado',
        'activo',
        'fallecido'
    ]

    # Campos para búsqueda
    search_fields = [
        'nombre',
        'tutor__first_name',
        'tutor__last_name',
        'microchip',
        'color'
    ]

    # Campos para ordenamiento
    ordering_fields = ['nombre', 'fecha_nacimiento', 'fecha_registro']
    ordering = ['-fecha_registro']

    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return MascotaListSerializer
        elif self.action == 'retrieve':
            return MascotaDetailSerializer
        return MascotaSerializer

    def get_queryset(self):
        """
        Filtra el queryset según el rol del usuario
        Los tutores solo ven sus propias mascotas
        """
        queryset = super().get_queryset()

        # Si el usuario es tutor, solo mostrar sus mascotas
        if self.request.user.es_tutor:
            return queryset.filter(tutor=self.request.user)

        # Personal puede ver todas las mascotas
        return queryset

    @action(detail=False, methods=['get'])
    def mis_mascotas(self, request):
        """
        Endpoint para obtener las mascotas del usuario actual
        GET /api/v1/pacientes/mascotas/mis-mascotas/
        """
        mascotas = self.queryset.filter(tutor=request.user, activo=True)
        serializer = MascotaListSerializer(mascotas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def marcar_fallecido(self, request, pk=None):
        """
        Marca una mascota como fallecida
        POST /api/v1/pacientes/mascotas/{id}/marcar_fallecido/
        Body: { "fecha_fallecimiento": "2024-01-15" }
        """
        mascota = self.get_object()
        fecha_fallecimiento = request.data.get('fecha_fallecimiento')

        if not fecha_fallecimiento:
            return Response(
                {'error': 'Debe proporcionar la fecha de fallecimiento'},
                status=status.HTTP_400_BAD_REQUEST
            )

        mascota.fallecido = True
        mascota.fecha_fallecimiento = fecha_fallecimiento
        mascota.activo = False
        mascota.save()

        return Response(
            {'status': 'Mascota marcada como fallecida'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def actualizar_peso(self, request, pk=None):
        """
        Actualiza el peso actual de la mascota
        POST /api/v1/pacientes/mascotas/{id}/actualizar_peso/
        Body: { "peso": 15.5 }
        """
        mascota = self.get_object()
        peso = request.data.get('peso')

        if not peso:
            return Response(
                {'error': 'Debe proporcionar el peso'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            mascota.peso_actual = float(peso)
            mascota.save()
            return Response(
                {
                    'status': 'Peso actualizado exitosamente',
                    'peso_actual': mascota.peso_actual
                },
                status=status.HTTP_200_OK
            )
        except ValueError:
            return Response(
                {'error': 'El peso debe ser un número válido'},
                status=status.HTTP_400_BAD_REQUEST
            )
