"""
Celery configuration for RamboPet project.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('rambopet')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule (Scheduled Tasks)
app.conf.beat_schedule = {
    # Check inventory stock levels every day at 8:00 AM
    'check-inventory-stock-daily': {
        'task': 'inventario.tasks.check_stock_levels',
        'schedule': crontab(hour=8, minute=0),
    },
    # Send appointment reminders every day at 9:00 AM
    'send-appointment-reminders-daily': {
        'task': 'citas.tasks.send_appointment_reminders',
        'schedule': crontab(hour=9, minute=0),
    },
    # Check for expiring products every week on Monday at 10:00 AM
    'check-expiring-products-weekly': {
        'task': 'inventario.tasks.check_expiring_products',
        'schedule': crontab(hour=10, minute=0, day_of_week=1),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')
