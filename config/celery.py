from __future__ import absolute_import, unicode_literals
from celery import Celery
from datetime import timedelta
from django.conf import settings


user = settings.RABBITMQ_USER
password = settings.RABBITMQ_PASSWORD
host = settings.RABBITMQ_HOST
port = settings.RABBITMQ_PORT
vhost = settings.RABBITMQ_VHOST
interval_time = settings.INTERVAL_TIME

# 设置为 celery 后端消息队列
BROKER_URL = f'amqp://{user}:{password}@{host}:{port}/{vhost}'


app = Celery('app',broker=BROKER_URL,include=['config.cron_update'])
app.conf.timezone = 'Asia/Shanghai'

app.conf.enable_utc = False



app.conf.beat_schedule = {
    'low-task': {
        'task': 'config.cron_update.update_file',
        'schedule': timedelta(minutes=int(interval_time)),
        'args': (),
    }
}