import logging
import sys
from datetime import datetime
from .config import settings

def setup_logging():
    
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                f"sync_service_{datetime.now().strftime('%Y%m%d')}.log",
                mode='a'
            )
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized")
    
    return logger