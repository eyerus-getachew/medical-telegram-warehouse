from src.utils.logger import setup_logger

logger = setup_logger()

logger.info("Scraper started.")
logger.warning("This is a warning.")
logger.error("This is an error.")