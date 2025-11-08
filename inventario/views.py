"""
Views para la aplicación Inventario
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum, Count, Q
from datetime import timedelta
from django.utils import timezone
from .models import Producto, Lote, MovimientoInventario
from .serializers import (
    ProductoSerializer,
    ProductoListSerializer,
    LoteSerializer,
    LoteListSerializer,
    MovimientoInventarioSerializer,
    StockReportSerializer
)


class ProductoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de productos

    Endpoints:
    - GET /api/v1/inventario/productos/ - Lista todos los productos
    - POST /api/v1/inventario/productos/ - Crea un nuevo producto
    - GET /api/v1/inventario/productos/{id}/ - Obtiene un producto específico
    - PUT/PATCH /api/v1/inventario/productos/{id}/ - Actualiza un producto
    - DELETE /api/v1/inventario/productos/{id}/ - Elimina un producto
    - GET /api/v1/inventario/productos/stock-bajo/ - Productos con stock bajo
    - GET /api/v1/inventario/productos/reporte-stock/ - Reporte general de stock
    """

    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # Campos para filtrado
    filterset_fields = ['categoria', 'activo', 'requiere_receta']

    # Campos para búsqueda
    search_fields = [
        'codigo',
        'nombre',
        'descripcion',
        'principio_activo',
        'laboratorio'
    ]

    # Campos para ordenamiento
    ordering_fields = ['codigo', 'nombre', 'categoria']
    ordering = ['nombre']

    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return ProductoListSerializer
        return ProductoSerializer

    @action(detail=False, methods=['get'])
    def stock_bajo(self, request):
        """
        Obtiene productos con stock bajo
        GET /api/v1/inventario/productos/stock-bajo/
        """
        productos = []
        for producto in self.queryset.filter(activo=True):
            if producto.tiene_stock_bajo:
                productos.append(producto)

        serializer = ProductoListSerializer(productos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def reporte_stock(self, request):
        """
        Genera un reporte general de stock
        GET /api/v1/inventario/productos/reporte-stock/
        """
        productos = self.queryset.filter(activo=True)
        reporte = []

        for producto in productos:
            stock_total = producto.stock_total
            cantidad_lotes = producto.lotes.filter(activo=True).count()

            # Determinar estado
            if stock_total == 0:
                estado = 'SIN_STOCK'
            elif stock_total < producto.stock_minimo:
                estado = 'STOCK_BAJO'
            elif stock_total > producto.stock_maximo:
                estado = 'SOBRESTOCK'
            else:
                estado = 'NORMAL'

            reporte.append({
                'producto_id': producto.id,
                'producto_codigo': producto.codigo,
                'producto_nombre': producto.nombre,
                'categoria': producto.get_categoria_display(),
                'stock_total': stock_total,
                'stock_minimo': producto.stock_minimo,
                'stock_maximo': producto.stock_maximo,
                'estado': estado,
                'cantidad_lotes': cantidad_lotes
            })

        serializer = StockReportSerializer(reporte, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def historial_movimientos(self, request, pk=None):
        """
        Obtiene el historial de movimientos de un producto
        GET /api/v1/inventario/productos/{id}/historial_movimientos/
        """
        producto = self.get_object()
        lotes = producto.lotes.all()

        movimientos = MovimientoInventario.objects.filter(
            lote__in=lotes
        ).select_related('lote', 'realizado_por').order_by('-fecha_movimiento')

        # Paginación opcional
        limit = request.query_params.get('limit', 50)
        movimientos = movimientos[:int(limit)]

        serializer = MovimientoInventarioSerializer(movimientos, many=True)
        return Response(serializer.data)


class LoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de lotes

    Endpoints:
    - GET /api/v1/inventario/lotes/ - Lista todos los lotes
    - POST /api/v1/inventario/lotes/ - Crea un nuevo lote
    - GET /api/v1/inventario/lotes/{id}/ - Obtiene un lote específico
    - PUT/PATCH /api/v1/inventario/lotes/{id}/ - Actualiza un lote
    - DELETE /api/v1/inventario/lotes/{id}/ - Elimina un lote
    - GET /api/v1/inventario/lotes/vencidos/ - Lotes vencidos
    - GET /api/v1/inventario/lotes/proximos-vencer/ - Lotes próximos a vencer
    """

    queryset = Lote.objects.select_related('producto')
    serializer_class = LoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # Campos para filtrado
    filterset_fields = ['producto', 'activo']

    # Campos para búsqueda
    search_fields = ['numero_lote', 'producto__nombre', 'proveedor']

    # Campos para ordenamiento
    ordering_fields = ['fecha_vencimiento', 'fecha_ingreso', 'stock_actual']
    ordering = ['fecha_vencimiento']

    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return LoteListSerializer
        return LoteSerializer

    @action(detail=False, methods=['get'])
    def vencidos(self, request):
        """
        Obtiene lotes vencidos
        GET /api/v1/inventario/lotes/vencidos/
        """
        today = timezone.now().date()
        lotes = self.queryset.filter(
            fecha_vencimiento__lt=today,
            stock_actual__gt=0,
            activo=True
        )

        serializer = LoteListSerializer(lotes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def proximos_vencer(self, request):
        """
        Obtiene lotes próximos a vencer (siguientes 30 días)
        GET /api/v1/inventario/lotes/proximos-vencer/
        """
        dias = int(request.query_params.get('dias', 30))
        today = timezone.now().date()
        fecha_limite = today + timedelta(days=dias)

        lotes = self.queryset.filter(
            fecha_vencimiento__gte=today,
            fecha_vencimiento__lte=fecha_limite,
            stock_actual__gt=0,
            activo=True
        )

        serializer = LoteListSerializer(lotes, many=True)
        return Response(serializer.data)


class MovimientoInventarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de movimientos de inventario

    Endpoints:
    - GET /api/v1/inventario/movimientos/ - Lista todos los movimientos
    - POST /api/v1/inventario/movimientos/ - Registra un nuevo movimiento
    - GET /api/v1/inventario/movimientos/{id}/ - Obtiene un movimiento específico
    - GET /api/v1/inventario/movimientos/por-producto/{producto_id}/ - Movimientos de un producto
    """

    queryset = MovimientoInventario.objects.select_related(
        'lote__producto',
        'realizado_por',
        'episodio_clinico'
    )
    serializer_class = MovimientoInventarioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # Campos para filtrado
    filterset_fields = ['lote', 'tipo_movimiento']

    # Campos para búsqueda
    search_fields = [
        'lote__producto__nombre',
        'lote__numero_lote',
        'motivo',
        'documento_referencia'
    ]

    # Campos para ordenamiento
    ordering_fields = ['fecha_movimiento']
    ordering = ['-fecha_movimiento']

    def perform_create(self, serializer):
        """Guarda el usuario que realizó el movimiento"""
        serializer.save(realizado_por=self.request.user)

    @action(detail=False, methods=['get'], url_path='por-producto/(?P<producto_id>[^/.]+)')
    def por_producto(self, request, producto_id=None):
        """
        Obtiene movimientos de un producto específico
        GET /api/v1/inventario/movimientos/por-producto/{producto_id}/
        """
        movimientos = self.queryset.filter(lote__producto_id=producto_id)

        # Paginación opcional
        limit = request.query_params.get('limit', 100)
        movimientos = movimientos[:int(limit)]

        serializer = self.get_serializer(movimientos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def registrar_entrada(self, request):
        """
        Registra una entrada de inventario
        POST /api/v1/inventario/movimientos/registrar_entrada/
        Body: {
            "lote": 1,
            "cantidad": 100,
            "motivo": "Compra",
            "documento_referencia": "FAC-001"
        }
        """
        data = request.data.copy()
        data['tipo_movimiento'] = MovimientoInventario.TipoMovimiento.ENTRADA

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(realizado_por=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def registrar_salida(self, request):
        """
        Registra una salida de inventario
        POST /api/v1/inventario/movimientos/registrar_salida/
        Body: {
            "lote": 1,
            "cantidad": 10,
            "motivo": "Uso en consulta",
            "episodio_clinico": 5
        }
        """
        data = request.data.copy()
        tipo_salida = request.data.get('tipo_salida', 'SALIDA_USO')

        # Validar tipo de salida
        if tipo_salida not in ['SALIDA_VENTA', 'SALIDA_USO']:
            return Response(
                {'error': 'Tipo de salida inválido. Use SALIDA_VENTA o SALIDA_USO'},
                status=status.HTTP_400_BAD_REQUEST
            )

        data['tipo_movimiento'] = tipo_salida

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(realizado_por=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Deshabilita la eliminación de movimientos para mantener trazabilidad"""
        return Response(
            {'error': 'No se pueden eliminar movimientos de inventario para mantener la trazabilidad'},
            status=status.HTTP_403_FORBIDDEN
        )
