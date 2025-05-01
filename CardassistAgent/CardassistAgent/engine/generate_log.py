import os
import yaml
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

config_path = os.getcwd()
default_log_level = 'INFO'
file_rotation = 'D'
file_rotation_interval = 1
backupCount = 5

log_directory = f"{config_path}/logs"
base_log_file_path = f"{log_directory}/Engine_logs_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
os.makedirs(log_directory, exist_ok=True)
handler = TimedRotatingFileHandler(base_log_file_path, when=file_rotation, interval=file_rotation_interval, backupCount=backupCount)
handler.suffix = "%Y%m%d%H%M%S"
handler.setFormatter(logging.Formatter("[%(asctime)s] [%(thread)d:%(threadName)s] [%(filename)s:%(lineno)d] %(levelname)s - %(message)s"))
logger = logging.getLogger("EngineLogger")
logger.addHandler(handler)
logger.setLevel(default_log_level)

