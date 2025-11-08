"""
Tareas de Celery para la aplicación Citas
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import Cita


@shared_task
def send_appointment_reminders():
    """
    Tarea programada para enviar recordatorios de citas
    Se ejecuta diariamente para citas del día siguiente
    """
    # Obtener citas para mañana que no han sido recordadas
    tomorrow = timezone.now() + timedelta(days=1)
    tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)

    citas = Cita.objects.filter(
        fecha_hora__gte=tomorrow_start,
        fecha_hora__lte=tomorrow_end,
        estado__in=[Cita.Estado.RESERVADA, Cita.Estado.CONFIRMADA],
        recordatorio_enviado=False
    ).select_related('mascota', 'tutor', 'medico')

    count = 0
    for cita in citas:
        try:
            # Enviar email al tutor
            subject = f'Recordatorio de Cita - {cita.mascota.nombre}'
            message = f"""
            Estimado/a {cita.tutor.get_full_name()},

            Le recordamos que tiene una cita programada para su mascota {cita.mascota.nombre}.

            Detalles de la cita:
            - Fecha y Hora: {cita.fecha_hora.strftime('%d/%m/%Y a las %H:%M')}
            - Tipo de Cita: {cita.get_tipo_cita_display()}
            - Médico: {cita.medico.get_full_name() if cita.medico else 'Por asignar'}
            - Motivo: {cita.motivo}

            Por favor, llegue 10 minutos antes de su cita.

            Si necesita cancelar o reprogramar, por favor contáctenos lo antes posible.

            Saludos,
            Clínica Veterinaria RamboPet
            """

            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [cita.tutor.email],
                fail_silently=False,
            )

            # Marcar como recordatorio enviado
            cita.recordatorio_enviado = True
            cita.fecha_recordatorio = timezone.now()
            cita.save()

            count += 1

        except Exception as e:
            # Log del error (en producción usar logging)
            print(f"Error enviando recordatorio para cita {cita.id}: {str(e)}")

    return f"Se enviaron {count} recordatorios de citas"


@shared_task
def check_expired_appointments():
    """
    Tarea para revisar citas vencidas y actualizarlas
    """
    # Obtener citas vencidas (pasaron hace más de 1 hora y siguen en estado RESERVADA o CONFIRMADA)
    expired_time = timezone.now() - timedelta(hours=1)

    citas_vencidas = Cita.objects.filter(
        fecha_hora__lt=expired_time,
        estado__in=[Cita.Estado.RESERVADA, Cita.Estado.CONFIRMADA]
    )

    count = citas_vencidas.update(estado=Cita.Estado.NO_ASISTIO)

    return f"Se marcaron {count} citas como NO_ASISTIO"


@shared_task
def send_daily_schedule_to_doctors():
    """
    Envía la agenda del día a cada médico
    """
    from usuarios.models import User

    today = timezone.now()
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Obtener todos los médicos activos
    medicos = User.objects.filter(rol=User.Rol.MEDICO, activo=True)

    count = 0
    for medico in medicos:
        # Obtener citas del día para este médico
        citas = Cita.objects.filter(
            medico=medico,
            fecha_hora__gte=today_start,
            fecha_hora__lte=today_end
        ).exclude(
            estado__in=[Cita.Estado.CANCELADA, Cita.Estado.NO_ASISTIO]
        ).select_related('mascota', 'tutor').order_by('fecha_hora')

        if citas.exists():
            # Construir el mensaje con la agenda
            citas_list = '\n'.join([
                f"- {cita.fecha_hora.strftime('%H:%M')} - {cita.mascota.nombre} "
                f"({cita.tutor.get_full_name()}) - {cita.get_tipo_cita_display()}"
                for cita in citas
            ])

            subject = f'Agenda del día - {today.strftime("%d/%m/%Y")}'
            message = f"""
            Estimado/a Dr./Dra. {medico.get_full_name()},

            Le enviamos su agenda del día de hoy {today.strftime('%d/%m/%Y')}:

            {citas_list}

            Total de citas: {citas.count()}

            Saludos,
            Sistema RamboPet
            """

            try:
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [medico.email],
                    fail_silently=False,
                )
                count += 1
            except Exception as e:
                print(f"Error enviando agenda a {medico.email}: {str(e)}")

    return f"Se enviaron {count} agendas a médicos"
