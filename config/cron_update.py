from .celery import app
from bk_framework_app.save_and_search import update_local_file
from blueapps.utils.logger import logger
import datetime


@app.task
def update_file():
    logger.info(f"{datetime.datetime.now()} - start update local file")
    update_local_file()
    logger.info(f"{datetime.datetime.now()} - end update local file")
    return "更新结束"
