"""
Modelos de la aplicación Inventario
Maneja productos, lotes, movimientos de inventario y alertas de stock
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta


class Producto(models.Model):
    """
    Modelo para los productos del inventario
    (Medicamentos, suministros, alimentos, etc.)
    """

    class Categoria(models.TextChoices):
        MEDICAMENTO = 'MEDICAMENTO', 'Medicamento'
        VACUNA = 'VACUNA', 'Vacuna'
        SUMINISTRO_MEDICO = 'SUMINISTRO_MEDICO', 'Suministro Médico'
        ALIMENTO = 'ALIMENTO', 'Alimento'
        HIGIENE = 'HIGIENE', 'Higiene'
        ACCESORIO = 'ACCESORIO', 'Accesorio'
        OTRO = 'OTRO', 'Otro'

    class UnidadMedida(models.TextChoices):
        UNIDAD = 'UNIDAD', 'Unidad'
        CAJA = 'CAJA', 'Caja'
        FRASCO = 'FRASCO', 'Frasco'
        AMPOLLA = 'AMPOLLA', 'Ampolla'
        TABLETA = 'TABLETA', 'Tableta'
        CAPSULA = 'CAPSULA', 'Cápsula'
        ML = 'ML', 'Mililitros'
        GR = 'GR', 'Gramos'
        KG = 'KG', 'Kilogramos'

    # Información básica del producto
    codigo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Código del Producto',
        help_text='Código único identificador del producto'
    )

    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre del Producto'
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )

    categoria = models.CharField(
        max_length=20,
        choices=Categoria.choices,
        default=Categoria.OTRO,
        verbose_name='Categoría'
    )

    # Información farmacéutica (para medicamentos)
    principio_activo = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Principio Activo',
        help_text='Componente activo principal (para medicamentos)'
    )

    concentracion = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Concentración',
        help_text='Ej: 500mg, 10ml'
    )

    laboratorio = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Laboratorio/Fabricante'
    )

    # Unidades y medidas
    unidad_medida = models.CharField(
        max_length=15,
        choices=UnidadMedida.choices,
        default=UnidadMedida.UNIDAD,
        verbose_name='Unidad de Medida'
    )

    # Control de stock
    stock_minimo = models.PositiveIntegerField(
        default=10,
        verbose_name='Stock Mínimo',
        help_text='Cantidad mínima antes de generar alerta'
    )

    stock_maximo = models.PositiveIntegerField(
        default=100,
        verbose_name='Stock Máximo',
        help_text='Cantidad máxima recomendada'
    )

    # Precios (opcional)
    precio_compra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Precio de Compra'
    )

    precio_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Precio de Venta'
    )

    # Configuración
    requiere_receta = models.BooleanField(
        default=False,
        verbose_name='Requiere Receta Médica'
    )

    control_lote = models.BooleanField(
        default=True,
        verbose_name='Control por Lote',
        help_text='Indica si el producto se controla por lotes y fechas de vencimiento'
    )

    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )

    # Campos de auditoría
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['categoria', 'activo']),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    @property
    def stock_total(self):
        """Calcula el stock total sumando todos los lotes activos"""
        return self.lotes.filter(activo=True).aggregate(
            total=models.Sum('stock_actual')
        )['total'] or 0

    @property
    def tiene_stock_bajo(self):
        """Verifica si el stock está por debajo del mínimo"""
        return self.stock_total < self.stock_minimo

    @property
    def lotes_proximos_vencer(self):
        """Retorna los lotes que vencen en los próximos 30 días"""
        fecha_limite = timezone.now().date() + timedelta(days=30)
        return self.lotes.filter(
            fecha_vencimiento__lte=fecha_limite,
            fecha_vencimiento__gt=timezone.now().date(),
            stock_actual__gt=0,
            activo=True
        )


class Lote(models.Model):
    """
    Modelo para los lotes de productos
    Permite el control de fechas de vencimiento y trazabilidad
    """

    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name='lotes',
        verbose_name='Producto'
    )

    numero_lote = models.CharField(
        max_length=100,
        verbose_name='Número de Lote'
    )

    fecha_fabricacion = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Fabricación'
    )

    fecha_vencimiento = models.DateField(
        verbose_name='Fecha de Vencimiento'
    )

    stock_inicial = models.PositiveIntegerField(
        verbose_name='Stock Inicial',
        help_text='Cantidad inicial del lote'
    )

    stock_actual = models.PositiveIntegerField(
        verbose_name='Stock Actual'
    )

    precio_compra_lote = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Precio de Compra del Lote'
    )

    proveedor = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Proveedor'
    )

    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )

    # Campos de auditoría
    fecha_ingreso = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Ingreso'
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )

    class Meta:
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'
        ordering = ['fecha_vencimiento']
        unique_together = ['producto', 'numero_lote']
        indexes = [
            models.Index(fields=['producto', 'fecha_vencimiento']),
            models.Index(fields=['fecha_vencimiento', 'activo']),
        ]

    def __str__(self):
        return f"Lote {self.numero_lote} - {self.producto.nombre}"

    @property
    def esta_vencido(self):
        """Verifica si el lote está vencido"""
        return self.fecha_vencimiento < timezone.now().date()

    @property
    def dias_para_vencer(self):
        """Calcula los días que faltan para el vencimiento"""
        delta = self.fecha_vencimiento - timezone.now().date()
        return delta.days

    @property
    def proximo_a_vencer(self):
        """Verifica si el lote vence en los próximos 30 días"""
        return 0 <= self.dias_para_vencer <= 30


class MovimientoInventario(models.Model):
    """
    Modelo para registrar todos los movimientos de inventario
    Proporciona trazabilidad completa
    """

    class TipoMovimiento(models.TextChoices):
        ENTRADA = 'ENTRADA', 'Entrada (Compra/Donación)'
        SALIDA_VENTA = 'SALIDA_VENTA', 'Salida por Venta'
        SALIDA_USO = 'SALIDA_USO', 'Salida por Uso Clínico'
        AJUSTE_POSITIVO = 'AJUSTE_POSITIVO', 'Ajuste Positivo'
        AJUSTE_NEGATIVO = 'AJUSTE_NEGATIVO', 'Ajuste Negativo'
        MERMA = 'MERMA', 'Merma/Vencimiento'
        DEVOLUCION = 'DEVOLUCION', 'Devolución'

    lote = models.ForeignKey(
        Lote,
        on_delete=models.PROTECT,
        related_name='movimientos',
        verbose_name='Lote'
    )

    tipo_movimiento = models.CharField(
        max_length=20,
        choices=TipoMovimiento.choices,
        verbose_name='Tipo de Movimiento'
    )

    cantidad = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Cantidad',
        help_text='Cantidad del movimiento (positivo o negativo)'
    )

    stock_anterior = models.PositiveIntegerField(
        verbose_name='Stock Anterior'
    )

    stock_nuevo = models.PositiveIntegerField(
        verbose_name='Stock Nuevo'
    )

    # Relación con episodio clínico (para salidas por uso clínico)
    episodio_clinico = models.ForeignKey(
        'hce.EpisodioClinico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_inventario',
        verbose_name='Episodio Clínico'
    )

    # Detalles del movimiento
    motivo = models.TextField(
        verbose_name='Motivo/Observaciones',
        help_text='Descripción del motivo del movimiento'
    )

    documento_referencia = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Documento de Referencia',
        help_text='Ej: Número de factura, orden de compra, etc.'
    )

    # Auditoría
    fecha_movimiento = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha del Movimiento'
    )

    realizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Realizado por'
    )

    class Meta:
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
        ordering = ['-fecha_movimiento']
        indexes = [
            models.Index(fields=['lote', '-fecha_movimiento']),
            models.Index(fields=['tipo_movimiento', '-fecha_movimiento']),
        ]

    def __str__(self):
        return f"{self.get_tipo_movimiento_display()} - {self.lote.producto.nombre} - {self.cantidad}"

    def save(self, *args, **kwargs):
        """Actualiza el stock del lote automáticamente"""
        # Si es un nuevo movimiento, calcular y actualizar stock
        if not self.pk:
            # Guardar stock anterior
            self.stock_anterior = self.lote.stock_actual

            # Calcular nuevo stock según el tipo de movimiento
            if self.tipo_movimiento in [
                self.TipoMovimiento.ENTRADA,
                self.TipoMovimiento.AJUSTE_POSITIVO,
                self.TipoMovimiento.DEVOLUCION
            ]:
                self.stock_nuevo = self.stock_anterior + self.cantidad
            else:
                self.stock_nuevo = self.stock_anterior - self.cantidad

            # Actualizar el stock del lote
            self.lote.stock_actual = self.stock_nuevo
            self.lote.save()

        super().save(*args, **kwargs)
