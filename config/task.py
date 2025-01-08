from config.cron_update import update_file
from celery.result import AsyncResult
from config.celery import app

res = update_file.delay()


