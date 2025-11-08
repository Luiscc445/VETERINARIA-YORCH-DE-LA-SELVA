"""
Views para la aplicación Citas
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Cita
from .serializers import (
    CitaSerializer,
    CitaListSerializer,
    CitaDetailSerializer,
    CitaCreateSerializer
)


class CitaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de citas

    Endpoints:
    - GET /api/v1/citas/ - Lista todas las citas
    - POST /api/v1/citas/ - Crea una nueva cita
    - GET /api/v1/citas/{id}/ - Obtiene una cita específica
    - PUT/PATCH /api/v1/citas/{id}/ - Actualiza una cita
    - DELETE /api/v1/citas/{id}/ - Elimina una cita
    - GET /api/v1/citas/mis-citas/ - Citas del usuario actual
    - GET /api/v1/citas/agenda-medico/ - Agenda del médico
    - GET /api/v1/citas/proximas/ - Próximas citas
    - POST /api/v1/citas/{id}/confirmar/ - Confirmar cita
    - POST /api/v1/citas/{id}/iniciar/ - Iniciar atención
    - POST /api/v1/citas/{id}/completar/ - Completar cita
    - POST /api/v1/citas/{id}/cancelar/ - Cancelar cita
    """

    queryset = Cita.objects.select_related('mascota', 'tutor', 'medico')
    serializer_class = CitaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # Campos para filtrado
    filterset_fields = [
        'mascota',
        'tutor',
        'medico',
        'estado',
        'tipo_cita',
        'fecha_hora'
    ]

    # Campos para búsqueda
    search_fields = [
        'mascota__nombre',
        'tutor__first_name',
        'tutor__last_name',
        'medico__first_name',
        'medico__last_name',
        'motivo'
    ]

    # Campos para ordenamiento
    ordering_fields = ['fecha_hora', 'fecha_creacion', 'estado']
    ordering = ['fecha_hora']

    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return CitaListSerializer
        elif self.action == 'retrieve':
            return CitaDetailSerializer
        elif self.action == 'create':
            return CitaCreateSerializer
        return CitaSerializer

    def get_queryset(self):
        """
        Filtra el queryset según el rol del usuario
        """
        queryset = super().get_queryset()
        user = self.request.user

        # Si el usuario es tutor, solo mostrar sus citas
        if user.es_tutor:
            return queryset.filter(tutor=user)

        # Si el usuario es médico, mostrar sus citas y las no asignadas
        if user.es_medico:
            return queryset.filter(
                models.Q(medico=user) | models.Q(medico__isnull=True)
            )

        # Personal administrativo ve todas las citas
        return queryset

    def perform_create(self, serializer):
        """Guarda el usuario que creó la cita"""
        serializer.save(creado_por=self.request.user)

    @action(detail=False, methods=['get'])
    def mis_citas(self, request):
        """
        Obtiene las citas del usuario actual
        GET /api/v1/citas/mis-citas/
        """
        user = request.user

        if user.es_tutor:
            citas = self.queryset.filter(tutor=user)
        elif user.es_medico:
            citas = self.queryset.filter(medico=user)
        else:
            return Response(
                {'error': 'Este endpoint solo está disponible para tutores y médicos'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Filtrar por estado si se proporciona
        estado = request.query_params.get('estado')
        if estado:
            citas = citas.filter(estado=estado)

        serializer = CitaListSerializer(citas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def agenda_medico(self, request):
        """
        Obtiene la agenda del médico para un día específico
        GET /api/v1/citas/agenda-medico/?fecha=2024-01-15&medico_id=1
        """
        # Obtener parámetros
        fecha_str = request.query_params.get('fecha')
        medico_id = request.query_params.get('medico_id')

        if not fecha_str:
            return Response(
                {'error': 'Debe proporcionar una fecha'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Filtrar citas
        citas = self.queryset.filter(
            fecha_hora__date=fecha
        ).exclude(
            estado__in=[Cita.Estado.CANCELADA, Cita.Estado.NO_ASISTIO]
        )

        if medico_id:
            citas = citas.filter(medico_id=medico_id)

        serializer = CitaListSerializer(citas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def proximas(self, request):
        """
        Obtiene las próximas citas (siguientes 7 días)
        GET /api/v1/citas/proximas/
        """
        dias = int(request.query_params.get('dias', 7))
        fecha_inicio = timezone.now()
        fecha_fin = fecha_inicio + timedelta(days=dias)

        citas = self.queryset.filter(
            fecha_hora__gte=fecha_inicio,
            fecha_hora__lte=fecha_fin
        ).exclude(
            estado__in=[Cita.Estado.CANCELADA, Cita.Estado.NO_ASISTIO]
        )

        # Filtrar por usuario según su rol
        user = request.user
        if user.es_tutor:
            citas = citas.filter(tutor=user)
        elif user.es_medico:
            citas = citas.filter(medico=user)

        serializer = CitaListSerializer(citas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        """
        Confirma una cita
        POST /api/v1/citas/{id}/confirmar/
        """
        cita = self.get_object()

        if cita.estado != Cita.Estado.RESERVADA:
            return Response(
                {'error': 'Solo se pueden confirmar citas en estado RESERVADA'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cita.confirmar()
        serializer = self.get_serializer(cita)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def iniciar(self, request, pk=None):
        """
        Inicia la atención de una cita
        POST /api/v1/citas/{id}/iniciar/
        """
        cita = self.get_object()

        if cita.estado not in [Cita.Estado.RESERVADA, Cita.Estado.CONFIRMADA]:
            return Response(
                {'error': 'Solo se pueden iniciar citas RESERVADAS o CONFIRMADAS'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cita.iniciar_atencion()
        serializer = self.get_serializer(cita)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def completar(self, request, pk=None):
        """
        Completa una cita
        POST /api/v1/citas/{id}/completar/
        """
        cita = self.get_object()

        if cita.estado != Cita.Estado.EN_CURSO:
            return Response(
                {'error': 'Solo se pueden completar citas EN_CURSO'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cita.completar()
        serializer = self.get_serializer(cita)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """
        Cancela una cita
        POST /api/v1/citas/{id}/cancelar/
        Body: { "motivo": "Motivo de la cancelación" }
        """
        cita = self.get_object()

        if not cita.puede_cancelarse:
            return Response(
                {'error': 'Esta cita no puede ser cancelada'},
                status=status.HTTP_400_BAD_REQUEST
            )

        motivo = request.data.get('motivo', '')
        cita.cancelar(motivo)
        serializer = self.get_serializer(cita)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def no_asistio(self, request, pk=None):
        """
        Marca una cita como no asistida
        POST /api/v1/citas/{id}/no_asistio/
        """
        cita = self.get_object()

        if cita.estado not in [Cita.Estado.RESERVADA, Cita.Estado.CONFIRMADA]:
            return Response(
                {'error': 'Solo se pueden marcar como no asistidas las citas RESERVADAS o CONFIRMADAS'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cita.marcar_no_asistio()
        serializer = self.get_serializer(cita)
        return Response(serializer.data)
