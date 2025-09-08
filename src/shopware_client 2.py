import requests
import logging
import hashlib
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
        """Authenticate with Shopware API and get access token."""
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
        """Get headers with authorization token."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def get_customer_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Check if customer exists by email."""
        url = f"{self.base_url}/api/customer"
        params = {
            "filter[email]": email
        }
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            customers = data.get("data", [])
            
            return customers[0] if customers else None
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to search customer by email {email}: {e}")
            raise
    
    def get_customer_by_customer_number(self, customer_number: str) -> Optional[Dict[str, Any]]:
        """Check if customer exists by customer number."""
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
    
    def _get_salutation_id(self) -> str:
        """Get salutation ID (default to 'not specified')."""
        url = f"{self.base_url}/api/salutation"
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            data = response.json()
            salutations = data.get("data", [])
            
            for salutation in salutations:
                if salutation.get("salutationKey") == "not_specified":
                    return salutation["id"]
            
            return salutations[0]["id"] if salutations else None
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to get salutation ID: {e}")
            return None
    
    def _get_sales_channel_id(self, channel_name: str = "Spotmarkt") -> str:
        """Get sales channel ID by name."""
        url = f"{self.base_url}/api/sales-channel"
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            data = response.json()
            channels = data.get("data", [])
            
            for channel in channels:
                if channel.get("name") == channel_name:
                    return channel["id"]
            
            return channels[0]["id"] if channels else None
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to get sales channel ID: {e}")
            return None
    
    def _get_customer_group_id(self, group_name: str = "Standard customer group") -> str:
        """Get customer group ID by name."""
        url = f"{self.base_url}/api/customer-group"
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            data = response.json()
            groups = data.get("data", [])
            
            for group in groups:
                if group.get("name") == group_name:
                    return group["id"]
            
            return groups[0]["id"] if groups else None
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to get customer group ID: {e}")
            return None
    
    def _get_country_id(self, iso_code: str) -> str:
        """Get country ID by ISO code from spotmarkt API."""
        url = "https://spotmarkt.meinvme.de/api/country"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            countries = data.get("data", [])
            
            for country in countries:
                if country.get("attributes", {}).get("iso", "").lower() == iso_code.lower():
                    return country["id"]
            
            return None
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to get country ID for {iso_code}: {e}")
            return None
    
    def _generate_password(self) -> str:
        """Generate a secure random password."""
        return secrets.token_urlsafe(16)
    
    def _create_address(self, admin_contact: Union[AdminPanelUser, AdminPanelZrContact], customer_id: str) -> str:
        """Create a customer address and return the address ID."""
        salutation_id = self._get_salutation_id()
        country_id = self._get_country_id(admin_user.land)
        
        if not all([salutation_id, country_id]):
            raise ValueError("Failed to get required address IDs")
        
        address_data = {
            "customerId": customer_id,
            "salutationId": salutation_id,
            "firstName": admin_user.vorname,
            "lastName": admin_user.name,
            "street": admin_user.strasse,
            "zipcode": admin_user.postleitzahl,
            "city": admin_user.stadt,
            "countryId": country_id,
            "company": f"{admin_user.firma} (ZR: {admin_user.zrNummer})"
        }
        
        url = f"{self.base_url}/api/customer-address"
        
        try:
            response = requests.post(url, headers=self._get_headers(), json=address_data, timeout=30)
            response.raise_for_status()
            
            address_response = response.json()
            return address_response["data"]["id"]
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to create address for customer {admin_user.eMailadresse}: {e}")
            raise
    
    def create_customer(self, admin_user: AdminPanelUser) -> Dict[str, Any]:
        """Create a new customer in Shopware with proper address handling."""
        salutation_id = self._get_salutation_id()
        sales_channel_id = self._get_sales_channel_id()
        customer_group_id = self._get_customer_group_id()
        
        if not all([salutation_id, sales_channel_id, customer_group_id]):
            raise ValueError("Failed to get required Shopware IDs")
        
        password = self._generate_password()
        
        customer_data = {
            "email": admin_user.eMailadresse,
            "password": password,
            "salutationId": salutation_id,
            "firstName": admin_user.vorname,
            "lastName": admin_user.name,
            "customerNumber": admin_user.zrNummer,
            "company": f"{admin_user.firma} ({admin_user.zrNummer})",
            "vatIds": [admin_user.uStID] if admin_user.uStID else [],
            "groupId": customer_group_id,
            "salesChannelId": sales_channel_id,
            "accountType": "business"
        }
        
        url = f"{self.base_url}/api/customer"
        
        try:
            response = requests.post(url, headers=self._get_headers(), json=customer_data, timeout=30)
            response.raise_for_status()
            
            customer_response = response.json()
            customer_id = customer_response["data"]["id"]
            
            address_id = self._create_address(admin_user, customer_id)
            
            address_types = admin_user.adresstyp.split(";")
            update_data = {}
            
            if "Rechnungsanschrift" in address_types:
                update_data["defaultBillingAddressId"] = address_id
            if "Lieferanschrift" in address_types:
                update_data["defaultShippingAddressId"] = address_id
            
            if update_data:
                update_url = f"{self.base_url}/api/customer/{customer_id}"
                update_response = requests.patch(update_url, headers=self._get_headers(), json=update_data, timeout=30)
                update_response.raise_for_status()
            
            self.logger.info(f"Successfully created customer: {admin_user.eMailadresse}")
            return customer_response
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to create customer {admin_user.eMailadresse}: {e}")
            raise
    
    def update_customer(self, admin_user: AdminPanelUser, existing_customer: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing customer in Shopware."""
        customer_id = existing_customer["id"]
        
        update_data = {
            "firstName": admin_user.vorname,
            "lastName": admin_user.name,
            "customerNumber": admin_user.zrNummer,
            "company": f"{admin_user.firma} ({admin_user.zrNummer})",
            "vatIds": [admin_user.uStID] if admin_user.uStID else [],
            "accountType": "business"
        }
        
        url = f"{self.base_url}/api/customer/{customer_id}"
        
        try:
            response = requests.patch(url, headers=self._get_headers(), json=update_data, timeout=30)
            response.raise_for_status()
            
            address_id = self._update_or_create_address(admin_user, customer_id, existing_customer)
            
            address_types = admin_user.adresstyp.split(";")
            address_update_data = {}
            
            if "Rechnungsanschrift" in address_types:
                address_update_data["defaultBillingAddressId"] = address_id
            if "Lieferanschrift" in address_types:
                address_update_data["defaultShippingAddressId"] = address_id
            
            if address_update_data:
                address_response = requests.patch(url, headers=self._get_headers(), json=address_update_data, timeout=30)
                address_response.raise_for_status()
            
            self.logger.info(f"Successfully updated customer: {admin_user.eMailadresse}")
            return response.json()
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to update customer {admin_user.eMailadresse}: {e}")
            raise
    
    def _update_or_create_address(self, admin_user: AdminPanelUser, customer_id: str, existing_customer: Dict[str, Any]) -> str:
        """Update existing address or create new one if needed."""
        
        existing_billing_id = existing_customer.get("attributes", {}).get("defaultBillingAddressId")
        existing_shipping_id = existing_customer.get("attributes", {}).get("defaultShippingAddressId")
        
        address_id_to_update = existing_billing_id or existing_shipping_id
        
        if address_id_to_update:
            return self._update_address(admin_user, address_id_to_update)
        else:
            return self._create_address(admin_user, customer_id)
    
    def _update_address(self, admin_user: AdminPanelUser, address_id: str) -> str:
        """Update an existing customer address."""
        country_id = self._get_country_id(admin_user.land)
        
        if not country_id:
            raise ValueError("Failed to get country ID for address update")
        
        address_data = {
            "firstName": admin_user.vorname,
            "lastName": admin_user.name,
            "street": admin_user.strasse,
            "zipcode": admin_user.postleitzahl,
            "city": admin_user.stadt,
            "countryId": country_id,
            "company": f"{admin_user.firma} (ZR: {admin_user.zrNummer})"
        }
        
        url = f"{self.base_url}/api/customer-address/{address_id}"
        
        try:
            response = requests.patch(url, headers=self._get_headers(), json=address_data, timeout=30)
            response.raise_for_status()
            
            return address_id
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to update address {address_id}: {e}")
            raise
    
    def upsert_customer(self, admin_user: AdminPanelUser) -> Dict[str, Any]:
        """Create or update a customer based on whether they exist."""
        existing_customer = self.get_customer_by_email(admin_user.eMailadresse)
        
        if existing_customer:
            return self.update_customer(admin_user, existing_customer)
        else:
            return self.create_customer(admin_user)