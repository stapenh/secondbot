import sys
from loguru import logger

log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

logger.remove()
# logger.add("app.log", rotation="500 MB", format=log_format)
logger.add(sink=sys.stdout, format=log_format, level="DEBUG")

logger.debug("logger init..")