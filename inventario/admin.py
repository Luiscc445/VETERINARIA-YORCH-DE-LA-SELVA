"""
Configuración del Admin para la aplicación Inventario
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import Producto, Lote, MovimientoInventario


class LoteInline(admin.TabularInline):
    """
    Inline para mostrar lotes dentro de productos
    """
    model = Lote
    extra = 1
    fields = (
        'numero_lote',
        'fecha_vencimiento',
        'stock_inicial',
        'stock_actual',
        'precio_compra_lote',
        'activo'
    )
    readonly_fields = ('stock_actual',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para Productos
    """

    list_display = (
        'codigo',
        'nombre',
        'categoria_badge',
        'stock_total_display',
        'stock_status',
        'precio_venta',
        'lotes_count',
        'activo'
    )

    list_filter = (
        'categoria',
        'activo',
        'control_lote',
        'requiere_receta'
    )

    search_fields = (
        'codigo',
        'nombre',
        'principio_activo',
        'laboratorio'
    )

    ordering = ('nombre',)

    list_editable = ('activo',)

    inlines = [LoteInline]

    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'categoria')
        }),
        ('Información Farmacéutica', {
            'fields': ('principio_activo', 'concentracion', 'laboratorio'),
            'classes': ('collapse',)
        }),
        ('Unidades y Medidas', {
            'fields': ('unidad_medida',)
        }),
        ('Control de Stock', {
            'fields': ('stock_minimo', 'stock_maximo', 'control_lote')
        }),
        ('Precios', {
            'fields': ('precio_compra', 'precio_venta'),
            'classes': ('collapse',)
        }),
        ('Configuración', {
            'fields': ('requiere_receta', 'activo')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')

    def categoria_badge(self, obj):
        """Muestra la categoría con un badge de color"""
        colors = {
            'MEDICAMENTO': '#007bff',
            'VACUNA': '#28a745',
            'SUMINISTRO_MEDICO': '#17a2b8',
            'ALIMENTO': '#ffc107',
            'HIGIENE': '#6610f2',
            'ACCESORIO': '#6c757d',
            'OTRO': '#343a40',
        }
        color = colors.get(obj.categoria, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_categoria_display()
        )
    categoria_badge.short_description = 'Categoría'

    def stock_total_display(self, obj):
        """Muestra el stock total"""
        stock = obj.stock_total
        return f"{stock} {obj.get_unidad_medida_display()}"
    stock_total_display.short_description = 'Stock Total'

    def stock_status(self, obj):
        """Muestra el estado del stock con colores"""
        stock = obj.stock_total
        if stock == 0:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">SIN STOCK</span>'
            )
        elif stock < obj.stock_minimo:
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">STOCK BAJO</span>'
            )
        elif stock > obj.stock_maximo:
            return format_html(
                '<span style="background-color: #17a2b8; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">SOBRESTOCK</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">NORMAL</span>'
            )
    stock_status.short_description = 'Estado'

    def lotes_count(self, obj):
        """Muestra la cantidad de lotes activos"""
        count = obj.lotes.filter(activo=True).count()
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 2px 8px; '
            'border-radius: 10px; font-size: 12px;">{}</span>',
            count
        )
    lotes_count.short_description = 'Lotes'

    def get_queryset(self, request):
        """Optimiza las consultas"""
        return super().get_queryset(request).prefetch_related('lotes')


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para Lotes
    """

    list_display = (
        'numero_lote',
        'producto_link',
        'fecha_vencimiento',
        'dias_vencimiento',
        'stock_display',
        'estado_badge',
        'activo'
    )

    list_filter = (
        'activo',
        'fecha_vencimiento',
        'fecha_ingreso',
        'producto__categoria'
    )

    search_fields = (
        'numero_lote',
        'producto__nombre',
        'producto__codigo',
        'proveedor'
    )

    ordering = ('fecha_vencimiento',)

    date_hierarchy = 'fecha_vencimiento'

    fieldsets = (
        ('Producto', {
            'fields': ('producto',)
        }),
        ('Información del Lote', {
            'fields': ('numero_lote', 'fecha_fabricacion', 'fecha_vencimiento')
        }),
        ('Stock', {
            'fields': ('stock_inicial', 'stock_actual')
        }),
        ('Información de Compra', {
            'fields': ('precio_compra_lote', 'proveedor'),
            'classes': ('collapse',)
        }),
        ('Configuración', {
            'fields': ('activo',)
        }),
        ('Auditoría', {
            'fields': ('fecha_ingreso', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('fecha_ingreso', 'fecha_actualizacion', 'stock_actual')

    def producto_link(self, obj):
        """Muestra el nombre del producto con enlace"""
        return format_html(
            '<a href="/admin/inventario/producto/{}/change/">{}</a>',
            obj.producto.id,
            obj.producto.nombre
        )
    producto_link.short_description = 'Producto'

    def stock_display(self, obj):
        """Muestra el stock con formato"""
        return f"{obj.stock_actual} / {obj.stock_inicial}"
    stock_display.short_description = 'Stock (Actual/Inicial)'

    def dias_vencimiento(self, obj):
        """Muestra los días para vencer"""
        dias = obj.dias_para_vencer
        if dias < 0:
            return format_html('<span style="color: #dc3545;">Vencido hace {} días</span>', abs(dias))
        elif dias == 0:
            return format_html('<span style="color: #dc3545; font-weight: bold;">Vence HOY</span>')
        elif dias <= 30:
            return format_html('<span style="color: #ffc107; font-weight: bold;">{} días</span>', dias)
        else:
            return format_html('<span style="color: #28a745;">{} días</span>', dias)
    dias_vencimiento.short_description = 'Vencimiento'

    def estado_badge(self, obj):
        """Muestra el estado del lote"""
        if obj.esta_vencido:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">VENCIDO</span>'
            )
        elif obj.proximo_a_vencer:
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 10px; '
                'border-radius: 3px; font-weight: bold;">PRÓX. VENCER</span>'
            )
        elif obj.stock_actual == 0:
            return format_html(
                '<span style="background-color: #6c757d; color: white; padding: 3px 10px; '
                'border-radius: 3px;">SIN STOCK</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px;">VIGENTE</span>'
            )
    estado_badge.short_description = 'Estado'

    def get_queryset(self, request):
        """Optimiza las consultas"""
        return super().get_queryset(request).select_related('producto')


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para Movimientos de Inventario
    """

    list_display = (
        'id',
        'fecha_movimiento',
        'tipo_badge',
        'producto_nombre',
        'lote_numero',
        'cantidad_display',
        'stock_cambio',
        'realizado_por'
    )

    list_filter = (
        'tipo_movimiento',
        'fecha_movimiento',
        'lote__producto__categoria'
    )

    search_fields = (
        'lote__producto__nombre',
        'lote__numero_lote',
        'motivo',
        'documento_referencia'
    )

    ordering = ('-fecha_movimiento',)

    date_hierarchy = 'fecha_movimiento'

    fieldsets = (
        ('Información del Movimiento', {
            'fields': ('lote', 'tipo_movimiento', 'cantidad')
        }),
        ('Stock', {
            'fields': ('stock_anterior', 'stock_nuevo'),
            'classes': ('collapse',)
        }),
        ('Detalles', {
            'fields': ('motivo', 'documento_referencia', 'episodio_clinico')
        }),
        ('Auditoría', {
            'fields': ('realizado_por', 'fecha_movimiento'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('fecha_movimiento', 'stock_anterior', 'stock_nuevo')

    def producto_nombre(self, obj):
        """Muestra el nombre del producto"""
        return obj.lote.producto.nombre
    producto_nombre.short_description = 'Producto'

    def lote_numero(self, obj):
        """Muestra el número de lote"""
        return obj.lote.numero_lote
    lote_numero.short_description = 'Lote'

    def tipo_badge(self, obj):
        """Muestra el tipo de movimiento con un badge"""
        colors = {
            'ENTRADA': '#28a745',
            'SALIDA_VENTA': '#007bff',
            'SALIDA_USO': '#17a2b8',
            'AJUSTE_POSITIVO': '#28a745',
            'AJUSTE_NEGATIVO': '#ffc107',
            'MERMA': '#dc3545',
            'DEVOLUCION': '#6610f2',
        }
        color = colors.get(obj.tipo_movimiento, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_tipo_movimiento_display()
        )
    tipo_badge.short_description = 'Tipo'

    def cantidad_display(self, obj):
        """Muestra la cantidad con signo"""
        if obj.tipo_movimiento in ['ENTRADA', 'AJUSTE_POSITIVO', 'DEVOLUCION']:
            return format_html('<span style="color: #28a745; font-weight: bold;">+{}</span>', obj.cantidad)
        else:
            return format_html('<span style="color: #dc3545; font-weight: bold;">-{}</span>', obj.cantidad)
    cantidad_display.short_description = 'Cantidad'

    def stock_cambio(self, obj):
        """Muestra el cambio de stock"""
        return f"{obj.stock_anterior} → {obj.stock_nuevo}"
    stock_cambio.short_description = 'Cambio de Stock'

    def get_queryset(self, request):
        """Optimiza las consultas"""
        return super().get_queryset(request).select_related(
            'lote__producto',
            'realizado_por',
            'episodio_clinico'
        )

    def has_delete_permission(self, request, obj=None):
        """Deshabilita la eliminación de movimientos para mantener trazabilidad"""
        return False
