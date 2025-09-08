import requests
import logging
from typing import List
from .models import AdminPanelUser, AdminPanelZrContact

class AdminPanelClient:
    def __init__(self, base_url: str, secret_header: str):
        self.base_url = base_url.rstrip('/')
        self.secret_header = secret_header
        self.logger = logging.getLogger(__name__)
    
    def get_all_contacts(self) -> List[AdminPanelUser]:
        url = f"{self.base_url}/api/contacts/list_contact_gs"
        headers = {
            "secretHeaderForAuth": self.secret_header,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            contacts_data = response.json()
            contacts = [AdminPanelUser(**contact) for contact in contacts_data
                        if contact.get('adresstyp') and contact.get('eMailadresse') and
                        contact.get('vorname') and contact.get('name') and contact.get('entraID') and contact.get('firma')
                        and contact.get('zrNummer') and contact.get('strasse') and contact.get('postleitzahl')
                        and contact.get('stadt') and contact.get('land')]
            
            self.logger.info(f"Successfully fetched {len(contacts)} contacts from admin panel")

            # MOCK TODO - FLZ
            contacts = [contact for contact in contacts if contact.eMailadresse == "thomas.kauer@kauer.ch"]

            return contacts
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch contacts from admin panel: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to parse contacts data: {e}")
            raise
    
    def get_all_zr_contacts(self) -> List[AdminPanelZrContact]:
        url = f"{self.base_url}/api/companys/list_gs_adresstyp"
        headers = {
            "secretHeaderForAuth": self.secret_header,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            zr_contacts_data = response.json()
            zr_contacts = [AdminPanelZrContact(**contact) for contact in zr_contacts_data
                            if contact.get('zrNummer') in ['112212', '112213', '112214']]
            
            self.logger.info(f"Successfully fetched {len(zr_contacts)} ZR contacts from admin panel")
            return zr_contacts
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch ZR contacts from admin panel: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to parse ZR contacts data: {e}")
            raise