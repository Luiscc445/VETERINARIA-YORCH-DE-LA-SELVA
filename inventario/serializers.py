"""
Serializers para la aplicación Inventario
"""

from rest_framework import serializers
from .models import Producto, Lote, MovimientoInventario


class ProductoSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Producto
    """
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    unidad_medida_display = serializers.CharField(source='get_unidad_medida_display', read_only=True)
    stock_total = serializers.IntegerField(read_only=True)
    tiene_stock_bajo = serializers.BooleanField(read_only=True)

    class Meta:
        model = Producto
        fields = [
            'id',
            'codigo',
            'nombre',
            'descripcion',
            'categoria',
            'categoria_display',
            'principio_activo',
            'concentracion',
            'laboratorio',
            'unidad_medida',
            'unidad_medida_display',
            'stock_minimo',
            'stock_maximo',
            'stock_total',
            'tiene_stock_bajo',
            'precio_compra',
            'precio_venta',
            'requiere_receta',
            'control_lote',
            'activo',
            'fecha_creacion',
            'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']

    def validate_codigo(self, value):
        """Valida que el código sea único"""
        # Si estamos actualizando, excluir el producto actual
        queryset = Producto.objects.filter(codigo=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Este código ya está en uso")
        return value


class LoteSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Lote
    """
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    esta_vencido = serializers.BooleanField(read_only=True)
    dias_para_vencer = serializers.IntegerField(read_only=True)
    proximo_a_vencer = serializers.BooleanField(read_only=True)

    class Meta:
        model = Lote
        fields = [
            'id',
            'producto',
            'producto_nombre',
            'numero_lote',
            'fecha_fabricacion',
            'fecha_vencimiento',
            'stock_inicial',
            'stock_actual',
            'precio_compra_lote',
            'proveedor',
            'esta_vencido',
            'dias_para_vencer',
            'proximo_a_vencer',
            'activo',
            'fecha_ingreso',
            'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'stock_actual', 'fecha_ingreso', 'fecha_actualizacion']

    def validate(self, attrs):
        """Validaciones personalizadas"""
        # Validar que fecha de vencimiento sea posterior a fabricación
        fecha_fab = attrs.get('fecha_fabricacion')
        fecha_venc = attrs.get('fecha_vencimiento')

        if fecha_fab and fecha_venc and fecha_venc <= fecha_fab:
            raise serializers.ValidationError({
                'fecha_vencimiento': 'La fecha de vencimiento debe ser posterior a la fabricación'
            })

        # El stock_actual se inicializa igual al stock_inicial
        if not self.instance and 'stock_inicial' in attrs:
            attrs['stock_actual'] = attrs['stock_inicial']

        return attrs


class MovimientoInventarioSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo MovimientoInventario
    """
    producto_nombre = serializers.CharField(source='lote.producto.nombre', read_only=True)
    lote_numero = serializers.CharField(source='lote.numero_lote', read_only=True)
    tipo_movimiento_display = serializers.CharField(source='get_tipo_movimiento_display', read_only=True)
    realizado_por_nombre = serializers.CharField(source='realizado_por.get_full_name', read_only=True)

    class Meta:
        model = MovimientoInventario
        fields = [
            'id',
            'lote',
            'producto_nombre',
            'lote_numero',
            'tipo_movimiento',
            'tipo_movimiento_display',
            'cantidad',
            'stock_anterior',
            'stock_nuevo',
            'episodio_clinico',
            'motivo',
            'documento_referencia',
            'fecha_movimiento',
            'realizado_por',
            'realizado_por_nombre'
        ]
        read_only_fields = [
            'id',
            'stock_anterior',
            'stock_nuevo',
            'fecha_movimiento'
        ]

    def validate_cantidad(self, value):
        """Valida que la cantidad sea positiva"""
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0")
        return value

    def validate(self, attrs):
        """Validaciones personalizadas"""
        lote = attrs.get('lote')
        tipo_movimiento = attrs.get('tipo_movimiento')
        cantidad = attrs.get('cantidad')

        # Para salidas, verificar que haya stock suficiente
        if tipo_movimiento in [
            MovimientoInventario.TipoMovimiento.SALIDA_VENTA,
            MovimientoInventario.TipoMovimiento.SALIDA_USO,
            MovimientoInventario.TipoMovimiento.AJUSTE_NEGATIVO,
            MovimientoInventario.TipoMovimiento.MERMA
        ]:
            if cantidad > lote.stock_actual:
                raise serializers.ValidationError({
                    'cantidad': f'Stock insuficiente. Stock actual: {lote.stock_actual}'
                })

        return attrs


class ProductoListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listados de productos
    """
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    stock_total = serializers.IntegerField(read_only=True)

    class Meta:
        model = Producto
        fields = [
            'id',
            'codigo',
            'nombre',
            'categoria',
            'categoria_display',
            'stock_total',
            'precio_venta',
            'activo'
        ]


class LoteListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listados de lotes
    """
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = Lote
        fields = [
            'id',
            'numero_lote',
            'producto_nombre',
            'fecha_vencimiento',
            'stock_actual',
            'activo'
        ]


class StockReportSerializer(serializers.Serializer):
    """
    Serializer para reportes de stock
    """
    producto_id = serializers.IntegerField()
    producto_codigo = serializers.CharField()
    producto_nombre = serializers.CharField()
    categoria = serializers.CharField()
    stock_total = serializers.IntegerField()
    stock_minimo = serializers.IntegerField()
    stock_maximo = serializers.IntegerField()
    estado = serializers.CharField()
    cantidad_lotes = serializers.IntegerField()
