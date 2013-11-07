import logging
import logging.config
from tater.core import config

logging.config.dictConfig(config.LOGGING_CONFIG)
logger = logging.getLogger('tater')