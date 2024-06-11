import requests

class MichaelsClient:

    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key

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

        headers = {
            "Api-Key": self.api_key
        }

        response = requests.get(self.base_url + endpoint, params=params, headers=headers)

        if not response.ok:
            response.raise_for_status()
        else:
            return response

    def update_inventories_by_seller_sku(self, updates: list[dict]):
        endpoint = "/listing/inventory/update-inventory-by-seller-sku-number"

        for i in range(0, len(updates), 50):
            headers = {
                "Api-Key": self.api_key
            }

            response = requests.post(self.base_url + endpoint, json=updates[i:min(i + 50, len(updates))], headers=headers)

            if not response.ok:
                response.raise_for_status()
                

    def update_price_by_seller_sku(self, requests):
        endpoint = "/listing/price/publish-by-seller-sku-number"

        headers = {
            "Api-Key": self.api_key
        }

        try:
            response = requests.post(self.base_url + endpoint, json=requests, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # Handle request errors
            print(f"Error updating price: {e}")
            raise
