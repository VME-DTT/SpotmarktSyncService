#!/usr/bin/env python3
import schedule
import time
import sys
from src.logger import setup_logging
from src.config import settings
from src.admin_panel_client import AdminPanelClient
from src.shopware_client import ShopwareClient
from src.sync_service import SyncService


def run_sync():
    logger = setup_logging()
    
    try:
        logger.info("Initializing sync service...")
        
        admin_client = AdminPanelClient(
            base_url=settings.admin_panel_url,
            secret_header=settings.admin_panel_secret
        )
        
        shopware_client = ShopwareClient(
            base_url=settings.shopware_url,
            client_id=settings.shopware_client_id,
            client_secret=settings.shopware_client_secret
        )
        
        sync_service = SyncService(admin_client, shopware_client)
        
        total, existing, created = sync_service.sync_users()
        logger.info(f"Sync completed successfully: {created} users created, {existing} already existed")

        total_zr, existing_zr, created_zr = sync_service.sync_zr_customers()
        logger.info(f"ZR Sync completed successfully: {created_zr} ZR customers created, {existing_zr} already existed")
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        sys.exit(1)


def main():
    logger = setup_logging()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        logger.info("Running sync once and exiting...")
        run_sync()
        return
    
    logger.info(f"Scheduling daily sync at {settings.sync_hour:02d}:{settings.sync_minute:02d}")
    
    schedule.every().day.at(f"{settings.sync_hour:02d}:{settings.sync_minute:02d}").do(run_sync)
    
    logger.info("Scheduler started. Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")


if __name__ == "__main__":
    main()