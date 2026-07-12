# logging_config.py
"""
Central logging setup. Call setup_logging() once, at process startup
(main.py), before anything else runs.

Logs go to both the console and a rotating file (logs/app.log) so you can
tail the console live and still have history to grep through afterwards.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

# Third-party libraries are noisy at INFO/DEBUG; keep them quiet unless
# something goes wrong so our own logs aren't drowned out.
_NOISY_LOGGERS = (
    "httpx",
    "httpcore",
    "telethon",
    "apscheduler",
    "openai",
    "openai.agents",
)


def setup_logging(level: int = logging.INFO) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    formatter = logging.Formatter(_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(console_handler)
    root.addHandler(file_handler)

    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    logging.getLogger(__name__).info("Logging initialized — writing to %s", LOG_FILE)
