from __future__ import absolute_import, unicode_literals
from celery import Celery
from datetime import timedelta
import os

RABBITMQ_VHOST = os.getenv('RABBITMQ_VHOST')
RABBITMQ_PORT = os.getenv('RABBITMQ_PORT')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_USER = os.getenv('RABBITMQ_USER')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD')

# 设置为 celery 后端消息队列
BROKER_URL = 'amqp://{user}:{password}@{host}:{port}/{vhost}'.format(
    user=RABBITMQ_USER,
    password=RABBITMQ_PASSWORD,
    host=RABBITMQ_HOST,
    port=RABBITMQ_PORT,
    vhost=RABBITMQ_VHOST,
)


app = Celery('app',broker=BROKER_URL,include=['config.cron_update'])
app.conf.timezone = 'Asia/Shanghai'

app.conf.enable_utc = False



app.conf.beat_schedule = {
    'low-task': {
        'task': 'config.cron_update.update_file',
        'schedule': timedelta(hours=1),
        'args': (),
    }
}