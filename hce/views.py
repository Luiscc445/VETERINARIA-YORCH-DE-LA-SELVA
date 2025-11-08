"""
Views para la aplicación HCE
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import EpisodioClinico, ConstantesVitales, Adjunto
from .serializers import (
    EpisodioClinicoSerializer,
    EpisodioClinicoListSerializer,
    EpisodioClinicoDetailSerializer,
    ConstantesVitalesSerializer,
    AdjuntoSerializer
)


class EpisodioClinicoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de episodios clínicos

    Endpoints:
    - GET /api/v1/hce/episodios/ - Lista todos los episodios
    - POST /api/v1/hce/episodios/ - Crea un nuevo episodio
    - GET /api/v1/hce/episodios/{id}/ - Obtiene un episodio específico
    - PUT/PATCH /api/v1/hce/episodios/{id}/ - Actualiza un episodio
    - DELETE /api/v1/hce/episodios/{id}/ - Elimina un episodio
    - GET /api/v1/hce/episodios/por-mascota/{mascota_id}/ - Historial de una mascota
    - POST /api/v1/hce/episodios/{id}/cerrar/ - Cierra el episodio
    """

    queryset = EpisodioClinico.objects.select_related(
        'cita',
        'mascota',
        'medico'
    ).prefetch_related('constantes_vitales', 'adjuntos')

    serializer_class = EpisodioClinicoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # Campos para filtrado
    filterset_fields = [
        'mascota',
        'medico',
        'pronostico',
        'episodio_cerrado'
    ]

    # Campos para búsqueda
    search_fields = [
        'mascota__nombre',
        'medico__first_name',
        'medico__last_name',
        'motivo_consulta',
        'diagnostico_presuntivo',
        'diagnostico_definitivo'
    ]

    # Campos para ordenamiento
    ordering_fields = ['fecha_creacion', 'proxima_revision']
    ordering = ['-fecha_creacion']

    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return EpisodioClinicoListSerializer
        elif self.action == 'retrieve':
            return EpisodioClinicoDetailSerializer
        return EpisodioClinicoSerializer

    def get_queryset(self):
        """
        Filtra el queryset según el rol del usuario
        """
        queryset = super().get_queryset()
        user = self.request.user

        # Si el usuario es tutor, solo mostrar episodios de sus mascotas
        if user.es_tutor:
            return queryset.filter(mascota__tutor=user)

        # Si el usuario es médico, mostrar sus episodios
        if user.es_medico:
            return queryset.filter(medico=user)

        # Personal administrativo ve todos los episodios
        return queryset

    @action(detail=False, methods=['get'], url_path='por-mascota/(?P<mascota_id>[^/.]+)')
    def por_mascota(self, request, mascota_id=None):
        """
        Obtiene el historial clínico completo de una mascota
        GET /api/v1/hce/episodios/por-mascota/{mascota_id}/
        """
        episodios = self.queryset.filter(mascota_id=mascota_id)

        # Verificar permisos: tutores solo ven sus mascotas
        if request.user.es_tutor:
            episodios = episodios.filter(mascota__tutor=request.user)

        serializer = EpisodioClinicoListSerializer(episodios, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cerrar(self, request, pk=None):
        """
        Cierra un episodio clínico
        POST /api/v1/hce/episodios/{id}/cerrar/
        """
        episodio = self.get_object()

        if episodio.episodio_cerrado:
            return Response(
                {'error': 'Este episodio ya está cerrado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        episodio.episodio_cerrado = True
        episodio.save()

        serializer = self.get_serializer(episodio)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reabrir(self, request, pk=None):
        """
        Reabre un episodio clínico cerrado
        POST /api/v1/hce/episodios/{id}/reabrir/
        """
        episodio = self.get_object()

        if not episodio.episodio_cerrado:
            return Response(
                {'error': 'Este episodio no está cerrado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        episodio.episodio_cerrado = False
        episodio.save()

        serializer = self.get_serializer(episodio)
        return Response(serializer.data)


class ConstantesVitalesViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de constantes vitales

    Endpoints:
    - GET /api/v1/hce/constantes/ - Lista todas las constantes
    - POST /api/v1/hce/constantes/ - Registra nuevas constantes
    - GET /api/v1/hce/constantes/{id}/ - Obtiene constantes específicas
    - PUT/PATCH /api/v1/hce/constantes/{id}/ - Actualiza constantes
    - DELETE /api/v1/hce/constantes/{id}/ - Elimina constantes
    """

    queryset = ConstantesVitales.objects.select_related('episodio', 'registrado_por')
    serializer_class = ConstantesVitalesSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]

    filterset_fields = ['episodio']
    ordering_fields = ['fecha_registro']
    ordering = ['-fecha_registro']

    def perform_create(self, serializer):
        """Guarda el usuario que registró las constantes"""
        serializer.save(registrado_por=self.request.user)


class AdjuntoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de adjuntos

    Endpoints:
    - GET /api/v1/hce/adjuntos/ - Lista todos los adjuntos
    - POST /api/v1/hce/adjuntos/ - Sube un nuevo adjunto
    - GET /api/v1/hce/adjuntos/{id}/ - Obtiene un adjunto específico
    - PUT/PATCH /api/v1/hce/adjuntos/{id}/ - Actualiza un adjunto
    - DELETE /api/v1/hce/adjuntos/{id}/ - Elimina un adjunto
    """

    queryset = Adjunto.objects.select_related('episodio', 'subido_por')
    serializer_class = AdjuntoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_fields = ['episodio', 'tipo']
    search_fields = ['titulo', 'descripcion']
    ordering_fields = ['fecha_subida']
    ordering = ['-fecha_subida']

    def perform_create(self, serializer):
        """Guarda el usuario que subió el adjunto"""
        serializer.save(subido_por=self.request.user)
