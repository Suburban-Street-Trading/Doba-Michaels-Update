import requests

class MichaelsClient:

    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Api-Key": api_key,
            "Content-Type": "application/json"
        }

    def get_all_listings(self):
        cursor = None
        listings = []

        while True:
            response = self._get_listings_page(cursor)
            data = response.json()

            listings.extend(data["data"]["listings"])

            cursor = data["data"]["nextCursor"]

            if not cursor:
                break

        return listings

    def _get_listings_page(self, cursor: str = None):
        endpoint = "/listing/all-listings"
        limit = 100

        params = {
            "limit": limit,
            "cursor": cursor
        }

        response = requests.get(self.base_url + endpoint, params=params, headers=self.headers)

        if not response.ok:
            response.raise_for_status()
        else:
            return response

    def update_inventories_by_seller_sku(self, updates: list[dict]):
        endpoint = "/listing/inventory/update-inventory-by-seller-sku-number"

        for i in range(0, len(updates), 50):

            response = requests.post(
                self.base_url + endpoint, 
                json=updates[i:min(i + 50, len(updates))], 
                headers=self.headers
            )

            if not response.ok:
                response.raise_for_status()
                

    def update_price_by_seller_sku(self, updates: list[dict]):
        endpoint = "/listing/price/publish-by-seller-sku-number"
        
        updates = [update for update in updates if update.get("price", 0) != 0]
        
        for i in range(0, len(updates), 50):
        
            response = requests.post(
                self.base_url + endpoint, 
                json=updates[i:min(i + 50, len(updates))], 
                headers=self.headers
            )
            
            if not response.ok:
                response.raise_for_status()        
                
                
    
