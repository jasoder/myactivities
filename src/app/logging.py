import logging
from app.enums import LogLevels

LOG_FORMAT_DEBUG = "%(levelname)s:%(message)s:%(pathname)s:%(funcName)s:%(lineno)d"


def configure_logging(log_level: str = LogLevels.error):
    log_level = str(log_level).upper()
    log_levels = list(LogLevels)

    if log_level not in log_levels:
        logging.basicConfig(level=LogLevels.error)
        return

    if log_level == LogLevels.debug:
        logging.basicConfig(level=log_level, format=LOG_FORMAT_DEBUG)
        return

    logging.basicConfig(level=log_level)