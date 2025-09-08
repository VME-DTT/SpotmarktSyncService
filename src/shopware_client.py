import requests
import logging
from uuid import uuid4
import secrets
from typing import Optional, List, Dict, Any, Union
from .models import AdminPanelUser, AdminPanelZrContact


class ShopwareClient:
    def __init__(self, base_url: str, client_id: str, client_secret: str):
        self.base_url = base_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.logger = logging.getLogger(__name__)
        self._authenticate()
    
    def _authenticate(self):
        url = f"{self.base_url}/api/oauth/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.logger.info("Successfully authenticated with Shopware API")
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to authenticate with Shopware: {e}")
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def get_customer_by_custom_field_entraid(self, identifier: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/api/customer"
        params = {
            "filter[customFields.custom_identifier_user_entraid_]": identifier
        }
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            customers = data.get("data", [])
            
            return customers[0] if customers else None
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to search customer by entra id {identifier}: {e}")
            raise
    
    def get_customer_by_customer_number(self, customer_number: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/api/customer"
        params = {
            "filter[customerNumber]": customer_number
        }
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            customers = data.get("data", [])
            
            return customers[0] if customers else None
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to search customer by number {customer_number}: {e}")
            raise
    
    def _get_customer_group_id(self, group_name: str = "Standard customer group") -> str:
        url = f"{self.base_url}/api/customer-group"
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            data = response.json()
            groups = data.get("data", [])
            
            for group in groups:
                if group.get("attributes", {}).get("name") == group_name:
                    return group["id"]
            
            return groups[0]["id"] if groups else None
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to get customer group ID: {e}")
            return None
    
    def _get_country_id(self, iso_code: str) -> str:
        url = "https://spotmarkt.meinvme.de/api/country"
        params = {
            "filter[iso]": iso_code.upper()
        }
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            countries = data.get("data", [])
            
            return countries[0].get("id") if countries else None
            
            return None
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to get country ID for {iso_code}: {e}")
            return None

    def create_customer(self, admin_user: AdminPanelUser):
        return self.create_customer_generic(admin_user, is_zr_contact=False)

    def create_zr_customer(self, zr_contact: AdminPanelZrContact):
        return self.create_customer_generic(zr_contact, is_zr_contact=True)

    def create_customer_generic(
            self,
            contact: Union[AdminPanelUser, AdminPanelZrContact],
            is_zr_contact: bool = False
    ):
        salutation_id = "0194f5c3188270cebd82c273d4142f1a"  # Default salutation ID for "not specified"
        sales_channel_id = "019523bfc9e77764a3373ddc1bafdb18"  # Default sales channel ID
        country_id = self._get_country_id(contact.land)
        customer_group_id = self._get_customer_group_id("ZR-Kunden" if is_zr_contact else "User-Kunden")

        if not all([salutation_id, sales_channel_id, customer_group_id]):
            raise ValueError("Failed to get required Shopware IDs")

        default_address_id = str(uuid4()).replace("-", "")

        customer_data = {
            "email": f"zr{contact.zrNummer}@einrichtungspartnerring.com" if is_zr_contact else getattr(contact, "eMailadresse", None),
            "salutationId": salutation_id,
            "firstName": None if is_zr_contact else contact.vorname,
            "lastName": None if is_zr_contact else contact.name,
            "customerNumber": contact.zrNummer,
            "company": f"{contact.firma} ({contact.zrNummer})",
            "vatIds": [contact.uStID] if contact.uStID else [],
            "groupId": customer_group_id,
            "salesChannelId": sales_channel_id,
            "accountType": "business",
            "languageId": "0194f5c317e673168b59b25c7f5514cc",  # Default language ID
            "defaultBillingAddressId": default_address_id,
            "defaultShippingAddressId": default_address_id,
            "defaultPaymentMethodId": "0197a6f28afe77af91a0c5e23c4c4633",  # Default payment method ID
            "addresses": [
                {
                    "id": default_address_id,
                    "firstName": None if is_zr_contact else contact.vorname,
                    "lastName": None if is_zr_contact else contact.name,
                    "street": contact.strasse,
                    "zipcode": contact.postleitzahl,
                    "city": contact.stadt,
                    "countryId": country_id,
                    "company": contact.firma,
                }
            ],
            "customFields": {
                "custom_identifier_user_entraid_": contact.entraID if not is_zr_contact else None,
            }
        }

        url = f"{self.base_url}/api/customer"

        try:
            response = requests.post(url, headers=self._get_headers(), json=customer_data, timeout=30)
            response.raise_for_status()

            contact_type = "ZR customer" if is_zr_contact else "customer"
            self.logger.info(f"Successfully created {contact_type}: {contact.zrNummer}")
            return

        except requests.RequestException as e:
            contact_type = "ZR customer" if is_zr_contact else "customer"
            self.logger.error(f"Failed to create {contact_type} {contact.zrNummer}: {e}")
            raise

    def update_customer(self, admin_user: AdminPanelUser, existing_customer: Dict[str, Any]):
        return self.update_customer_generic(admin_user, is_zr_contact=False, existing_customer=existing_customer)

    def update_zr_customer(self, zr_contact: AdminPanelZrContact, existing_customer: Dict[str, Any]):
        return self.update_customer_generic(zr_contact, is_zr_contact=True, existing_customer=existing_customer)

    def update_customer_generic(self,
            contact: Union[AdminPanelUser, AdminPanelZrContact],
            is_zr_contact: bool,
            existing_customer: Dict[str, Any]):
        customer_id = existing_customer["id"]
        default_address_id = existing_customer.get("attributes", {}).get("defaultBillingAddressId")
        salutation_id = "0194f5c3188270cebd82c273d4142f1a"  # Default salutation ID for "not specified"
        sales_channel_id = "019523bfc9e77764a3373ddc1bafdb18"  # Default sales channel ID
        customer_group_id = self._get_customer_group_id("ZR-Kunden" if is_zr_contact else "User-Kunden")
        country_id = self._get_country_id(contact.land)

        customer_data = {
            "email": f"zr{contact.zrNummer}@einrichtungspartnerring.com" if is_zr_contact else getattr(contact, "eMailadresse", None),
            "salutationId": salutation_id,
            "firstName": None if is_zr_contact else contact.vorname,
            "lastName": None if is_zr_contact else contact.name,
            "customerNumber": contact.zrNummer,
            "company": f"{contact.firma} ({contact.zrNummer})",
            "vatIds": [contact.uStID] if contact.uStID else [],
            "groupId": customer_group_id,
            "salesChannelId": sales_channel_id,
            "accountType": "business",
            "languageId": "0194f5c317e673168b59b25c7f5514cc",  # Default language ID
            "defaultBillingAddressId": default_address_id,
            "defaultShippingAddressId": default_address_id,
            "defaultPaymentMethodId": "0197a6f28afe77af91a0c5e23c4c4633",  # Default payment method ID
            "addresses": [
                {
                    "id": default_address_id,
                    "firstName": None if is_zr_contact else contact.vorname,
                    "lastName": None if is_zr_contact else contact.name,
                    "street": contact.strasse,
                    "zipcode": contact.postleitzahl,
                    "city": contact.stadt,
                    "countryId": country_id,
                    "company": contact.firma,
                }
            ]
        }
        
        url = f"{self.base_url}/api/customer/{customer_id}"
        
        try:
            response = requests.patch(url, headers=self._get_headers(), json=customer_data, timeout=30)
            response.raise_for_status()

            contact_type = "ZR customer" if is_zr_contact else "customer"
            self.logger.info(f"Successfully updated {contact_type}: {contact.zrNummer}")
            return

        except requests.RequestException as e:
            contact_type = "ZR customer" if is_zr_contact else "customer"
            self.logger.error(f"Failed to update {contact_type} {contact.zrNummer}: {e}")
            raise