"""
Tareas de Celery para la aplicación Inventario
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import Producto, Lote


@shared_task
def check_stock_levels():
    """
    Tarea programada para verificar niveles de stock
    Envía alertas cuando los productos están por debajo del stock mínimo
    """
    productos_bajo_stock = []

    for producto in Producto.objects.filter(activo=True):
        stock_total = producto.stock_total
        if stock_total < producto.stock_minimo:
            productos_bajo_stock.append({
                'codigo': producto.codigo,
                'nombre': producto.nombre,
                'stock_actual': stock_total,
                'stock_minimo': producto.stock_minimo,
                'categoria': producto.get_categoria_display()
            })

    if productos_bajo_stock:
        # Preparar mensaje de email
        productos_list = '\n'.join([
            f"- {p['codigo']} - {p['nombre']} ({p['categoria']}): "
            f"Stock actual: {p['stock_actual']}, Mínimo: {p['stock_minimo']}"
            for p in productos_bajo_stock
        ])

        subject = f'⚠️ Alerta de Stock Bajo - {len(productos_bajo_stock)} producto(s)'
        message = f"""
        Alerta de Stock Bajo en RamboPet

        Los siguientes productos están por debajo del stock mínimo:

        {productos_list}

        Por favor, revise el inventario y considere realizar un pedido.

        Sistema RamboPet
        """

        # Obtener emails de administradores
        from usuarios.models import User
        admin_emails = list(
            User.objects.filter(
                rol__in=[User.Rol.ADMIN, User.Rol.RECEPCION],
                activo=True
            ).values_list('email', flat=True)
        )

        if admin_emails:
            try:
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    admin_emails,
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error enviando alertas de stock: {str(e)}")

    return f"Se detectaron {len(productos_bajo_stock)} productos con stock bajo"


@shared_task
def check_expiring_products():
    """
    Tarea programada para verificar productos próximos a vencer
    Envía alertas cuando hay lotes que vencen en los próximos 30 días
    """
    today = timezone.now().date()
    fecha_limite = today + timedelta(days=30)

    # Lotes próximos a vencer
    lotes_proximos_vencer = Lote.objects.filter(
        fecha_vencimiento__gte=today,
        fecha_vencimiento__lte=fecha_limite,
        stock_actual__gt=0,
        activo=True
    ).select_related('producto').order_by('fecha_vencimiento')

    # Lotes vencidos con stock
    lotes_vencidos = Lote.objects.filter(
        fecha_vencimiento__lt=today,
        stock_actual__gt=0,
        activo=True
    ).select_related('producto')

    if lotes_proximos_vencer.exists() or lotes_vencidos.exists():
        # Preparar mensajes
        proximos_list = '\n'.join([
            f"- {lote.producto.codigo} - {lote.producto.nombre} "
            f"(Lote: {lote.numero_lote}): Vence el {lote.fecha_vencimiento.strftime('%d/%m/%Y')} "
            f"({lote.dias_para_vencer} días) - Stock: {lote.stock_actual}"
            for lote in lotes_proximos_vencer
        ])

        vencidos_list = '\n'.join([
            f"- {lote.producto.codigo} - {lote.producto.nombre} "
            f"(Lote: {lote.numero_lote}): Venció el {lote.fecha_vencimiento.strftime('%d/%m/%Y')} "
            f"- Stock: {lote.stock_actual} ⚠️"
            for lote in lotes_vencidos
        ])

        subject = f'⚠️ Alerta de Vencimientos - RamboPet'
        message = f"""
        Alerta de Vencimientos en RamboPet
        """

        if lotes_vencidos.exists():
            message += f"""

        ⛔ LOTES VENCIDOS CON STOCK ({lotes_vencidos.count()}):
        {vencidos_list}

        ACCIÓN REQUERIDA: Estos productos deben ser retirados del inventario inmediatamente.
        """

        if lotes_proximos_vencer.exists():
            message += f"""

        ⚠️ LOTES PRÓXIMOS A VENCER ({lotes_proximos_vencer.count()}):
        {proximos_list}

        ACCIÓN SUGERIDA: Priorice el uso de estos productos o considere devolución/descuento.
        """

        message += """

        Sistema RamboPet
        """

        # Obtener emails de administradores y médicos
        from usuarios.models import User
        staff_emails = list(
            User.objects.filter(
                rol__in=[User.Rol.ADMIN, User.Rol.MEDICO, User.Rol.RECEPCION],
                activo=True
            ).values_list('email', flat=True)
        )

        if staff_emails:
            try:
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    staff_emails,
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error enviando alertas de vencimiento: {str(e)}")

    return f"Lotes próximos a vencer: {lotes_proximos_vencer.count()}, Vencidos: {lotes_vencidos.count()}"


@shared_task
def generate_monthly_inventory_report():
    """
    Genera un reporte mensual del inventario
    """
    productos = Producto.objects.filter(activo=True)

    reporte_data = []
    total_valor_inventario = 0

    for producto in productos:
        stock_total = producto.stock_total
        valor_total = 0

        if producto.precio_compra:
            valor_total = float(stock_total) * float(producto.precio_compra)
            total_valor_inventario += valor_total

        reporte_data.append({
            'codigo': producto.codigo,
            'nombre': producto.nombre,
            'categoria': producto.get_categoria_display(),
            'stock': stock_total,
            'stock_minimo': producto.stock_minimo,
            'precio_compra': float(producto.precio_compra) if producto.precio_compra else 0,
            'valor_total': valor_total
        })

    # Preparar mensaje
    subject = f'📊 Reporte Mensual de Inventario - RamboPet'
    message = f"""
    Reporte Mensual de Inventario - {timezone.now().strftime('%B %Y')}

    Total de productos activos: {len(reporte_data)}
    Valor total estimado del inventario: ${total_valor_inventario:,.2f}

    Este es un reporte automático generado por el sistema.
    Para ver el detalle completo, ingrese al panel de administración.

    Sistema RamboPet
    """

    # Enviar a administradores
    from usuarios.models import User
    admin_emails = list(
        User.objects.filter(
            rol=User.Rol.ADMIN,
            activo=True
        ).values_list('email', flat=True)
    )

    if admin_emails:
        try:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                admin_emails,
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error enviando reporte mensual: {str(e)}")

    return f"Reporte generado: {len(reporte_data)} productos, Valor total: ${total_valor_inventario:,.2f}"
