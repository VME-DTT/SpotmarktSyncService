import logging
from typing import List, Tuple
from .admin_panel_client import AdminPanelClient
from .shopware_client import ShopwareClient
from .models import AdminPanelUser, AdminPanelZrContact


class SyncService:
    def __init__(self, admin_client: AdminPanelClient, shopware_client: ShopwareClient):
        self.admin_client = admin_client
        self.shopware_client = shopware_client
        self.logger = logging.getLogger(__name__)
    
    def sync_users(self) -> Tuple[int, int, int]:
        self.logger.info("Starting user synchronization")
        
        try:
            admin_users = self.admin_client.get_all_contacts()
            total_users = len(admin_users)
            updated_users = 0
            created_users = 0
            failed_users = 0
            
            self.logger.info(f"Processing {total_users} users from admin panel")
            
            for user in admin_users:
                try:
                    existing_customer = self.shopware_client.get_customer_by_custom_field_entraid(user.entraID)
                    
                    if existing_customer:
                        self.shopware_client.update_customer(user, existing_customer)
                        updated_users += 1
                        self.logger.info(f"Updated existing user: {user.eMailadresse}")
                    else:
                        self.shopware_client.create_customer(user)
                        created_users += 1
                        self.logger.info(f"Created new user: {user.eMailadresse}")
                
                except Exception as e:
                    failed_users += 1
                    self.logger.error(f"Failed to process user {user.eMailadresse}: {e}")
                    continue
            
            self.logger.info(
                f"Synchronization completed. Total: {total_users}, "
                f"Updated: {updated_users}, Created: {created_users}, Failed: {failed_users}"
            )
            
            return total_users, updated_users, created_users
            
        except Exception as e:
            self.logger.error(f"Synchronization failed: {e}")
            raise
    
    def sync_zr_customers(self) -> Tuple[int, int, int]:
        self.logger.info("Starting ZR customer synchronization")
        
        try:
            zr_contacts = self.admin_client.get_all_zr_contacts()
            total_contacts = len(zr_contacts)
            updated_contacts = 0
            created_contacts = 0
            failed_contacts = 0
            
            self.logger.info(f"Processing {total_contacts} ZR contacts from admin panel")
            
            for zr_contact in zr_contacts:
                try:
                    existing_customer = self.shopware_client.get_customer_by_customer_number(zr_contact.zrNummer)
                    
                    if existing_customer:
                        self.shopware_client.update_zr_customer(zr_contact, existing_customer)
                        updated_contacts += 1
                        self.logger.info(f"Updated existing ZR customer: {zr_contact.zrNummer}")
                    else:
                        self.shopware_client.create_zr_customer(zr_contact)
                        created_contacts += 1
                        self.logger.info(f"Created new ZR customer: {zr_contact.zrNummer}")
                
                except Exception as e:
                    failed_contacts += 1
                    self.logger.error(f"Failed to process ZR customer {zr_contact.zrNummer}: {e}")
                    continue
            
            self.logger.info(
                f"ZR synchronization completed. Total: {total_contacts}, "
                f"Updated: {updated_contacts}, Created: {created_contacts}, Failed: {failed_contacts}"
            )
            
            return total_contacts, updated_contacts, created_contacts
            
        except Exception as e:
            self.logger.error(f"ZR synchronization failed: {e}")
            raise