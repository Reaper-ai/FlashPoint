import logging
import sys
import os
from colorlog import ColoredFormatter
from pythonjsonlogger import jsonlogger

def setup_logger(name=__name__):
    logger = logging.getLogger(name)
    
    # Prevent duplicate logs if function is called multiple times
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)

    # 1. Check if we are in "Production" (Docker) or "Development" (Local)
    # We assume 'DOCKER_ENV' is set in your docker-compose.yaml
    if os.environ.get("DOCKER_ENV"):
        # JSON Formatter (Best for observability tools)
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s'
        )
    else:
        # Colored Formatter (Best for Hackathon Demo Videos)
        formatter = ColoredFormatter(
            "%(log_color)s%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
            reset=True,
            log_colors={
                'DEBUG':    'cyan',
                'INFO':     'green',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'red,bg_white',
            }
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger