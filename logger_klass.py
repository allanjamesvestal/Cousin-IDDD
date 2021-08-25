# Imports from python.
import logging


# Imports from this library.
from constants import PATHS


# all_loggers = [
#     logging.getLogger(name) for name in logging.root.manager.loggerDict
# ]

logging.getLogger("eyed3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("watchdog").setLevel(logging.WARNING)

# Create logger for the "podcast_metadata" application.
METADATA_LOGGER = logging.getLogger(name=None)
METADATA_LOGGER.setLevel(logging.DEBUG)

# Create file handler which logs all messages.
file_handler = logging.FileHandler(PATHS["stderr_logfile"])
file_handler.setLevel(logging.DEBUG)

METADATA_LOGGER.addHandler(file_handler)

# METADATA_LOGGER.info(all_loggers)
