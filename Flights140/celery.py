from __future__ import absolute_import
import os
from celery import Celery
from celery import shared_task
from celery.task.schedules import crontab
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Flights140.settings')
from django.conf import settings

# Indicate Celery to use the default Django settings module


app = Celery('Flights140')
app.config_from_object('django.conf:settings')

# This line will tell Celery to autodiscover all your tasks.py that are in your app folders
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
