import sys
from pathlib import Path
from loguru import logger

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"


def setup_logger():
    """configures logging to the console and file"""

    LOG_DIR.mkdir(exist_ok=True)

    logger.remove()

    # logs in console
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO")

    # logs in file
    log_file_path = LOG_DIR / "bot.log"

    logger.add(
        log_file_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO",
        rotation="5 MB",  # create a new file every 5 MB
        retention="14 days",  # keep logs for the last 2 weeks
        compression="zip"  # old logs are automatically archived
    )

    logger.info("Logger successfully configured. File writing enabled.")
