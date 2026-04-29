import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = BACKEND_DIR / "logs"
LOG_FILE = LOG_DIR / "procurement.log"

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    
    # Ensure logs directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    file = RotatingFileHandler(
        str(LOG_FILE),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file.setFormatter(formatter)
    logger.addHandler(console)
    logger.addHandler(file)
    logger.propagate = False
    return logger
