import os
from dotenv import load_dotenv

load_dotenv()

class Settings():
    admin_panel_url: str = os.getenv("ADMIN_PANEL_URL", "")
    admin_panel_secret: str = os.getenv("ADMIN_PANEL_SECRET", "")
    
    shopware_url: str = os.getenv("SHOPWARE_URL", "")
    shopware_client_id: str = os.getenv("SHOPWARE_CLIENT_ID", "")
    shopware_client_secret: str = os.getenv("SHOPWARE_CLIENT_SECRET", "")
    
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    sync_hour: int = int(os.getenv("SYNC_HOUR", "2"))
    sync_minute: int = int(os.getenv("SYNC_MINUTE", "0"))
    
    class Config:
        env_file = ".env"

settings = Settings()