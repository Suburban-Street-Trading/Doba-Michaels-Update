import json
import os
from dotenv import load_dotenv
import redis
import requests

load_dotenv()

MICHAELS_API_KEY = os.getenv("MICHAELS_API_KEY")

class MichaelsClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"Api-Key": api_key, "Content-Type": "application/json", "Accept": "*/*", "User-Agent": "PostmanRuntime/7.32.3"}

    def test_auth(self):
        endpoint = "/listing/authentication/test-auth"
        response = requests.get(self.base_url + endpoint, headers=self.headers)
        print(response.text)


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

        params = {"limit": limit, "cursor": cursor}

        response = requests.get(
            self.base_url + endpoint, params=params, headers=self.headers
        )

        if not response.ok:
            response.raise_for_status()
        else:
            return response

    def update_inventories_by_seller_sku(self, updates: list[dict]):
        endpoint = "/listing/inventory/update-inventory-by-seller-sku-number"

        for i in range(0, len(updates), 50):
            response = requests.post(
                self.base_url + endpoint,
                json=updates[i : min(i + 50, len(updates))],
                headers=self.headers,
            )

            if not response.ok:
                response.raise_for_status()

    def update_price_by_seller_sku(self, updates: list[dict]):
        endpoint = "/listing/price/publish-by-seller-sku-number"

        updates = [update for update in updates if update.get("price", 0) != 0]

        for i in range(0, len(updates), 50):
            response = requests.post(
                self.base_url + endpoint,
                json=updates[i : min(i + 50, len(updates))],
                headers=self.headers,
            )

            if not response.ok:
                response.raise_for_status()


client = MichaelsClient(
    "https://www.michaels.com/api/mkp/v1",
    "eyJhbGciOiJSUzUxMiJ9.eyJqdGkiOiIwYjRlZTA5MGY4NDM0YTRjOGRjMGNjNjRiZDA1OTg3NyIsIl9zZWxsZXJTdG9yZUlkIjoiMTQ3OTY3NDE3MDM5MzA2NzUyIiwiX2NyZWF0ZVRpbWUiOiIxNzU4MDMyMjYyMDIxIiwiX2V4cGlyZVRpbWUiOiIxNzY1ODY0Nzk5MDAwIiwiaXNzIjoibWRhLWFwaSIsInN1YiI6IjE0Nzk2NzQxNzAzOTMwNjc1MiIsImlhdCI6MTc1ODAzMjI2MiwiZXhwIjoxNzY1ODY0Nzk5LCJhdWQiOiJhcGlrZXkifQ.jA3hTGwuseIlH7cudTSvw9XSS6Xf1lPoJX7njLlqr4E8qrMg9_f22ULr0DGvh7RWO3yXprhSwaUVCCA_60s1Y354SYDg7Q2ZXPK1KlSaEPQToo4n-VO_zM2v5b6z_l0DjrPkW5dHII5by1jMXlGCoNmZb1K8ZztkMXV6OU3IYtlBs9sSVggX5gExeSOFToNXGA2q3piBAVziXVu0QQVFqwP6e2uPt0mFueXVxqgwenfmxSt4kn5D5hOf2qaixVAFyZGp3GnQmnbP5ntpw8KJKZtwBUtuO35dOpHkxOz7y71eDr4d5lJs2OMtfGeBCW_ghinlsl2povp_LH2WTU3cjA"
)

doba_redis = redis.Redis(host="localhost", port=6379, db=0, protocol=3)


def pulldown_listings():
    listings = client.get_all_listings()

    json_dict = {"listings": listings}

    file_path = os.path.join(os.path.dirname(__file__), "data/listings.json")
    with open(file_path, "w") as file:
        json.dump(json_dict, file)


def filter_doba_listings() -> list[dict]:
    listings_path = os.path.join(os.path.dirname(__file__), "data/listings.json")
    with open(listings_path, "r") as file:
        json_dict = json.load(file)

    doba_listings = [
        listing
        for listing in json_dict["listings"]
        if listing["sellerSkuNumber"][:2] == "Do"
        or listing["sellerSkuNumber"][:2] == "DB"
    ]

    return doba_listings


def filter_fox_listings() -> list[dict]:
    listings_path = os.path.join(os.path.dirname(__file__), "data/listings.json")
    with open(listings_path, "r") as file:
        json_dict = json.load(file)

    return [
        listing
        for listing in json_dict["listings"]
        if listing["sellerSkuNumber"][:3].upper() == "FOX"
    ]


def generate_new_sku_stocks():
    listings_path = os.path.join(os.path.dirname(__file__), "data/listings.json")
    with open(listings_path, "r") as file:
        listings = json.load(file)

    listings_lookup_dict = {
        listing["sellerSkuNumber"].split("-")[-1]: listing
        for listing in listings["listings"]
    }

    new_sku_stocks = []

    for stock in stocks:
        new_sku_stocks.append(
            {
                "sellerSkuNumber": listings_lookup_dict[stock["itemNo"]][
                    "sellerSkuNumber"
                ],
                "new_stock": stock["stock"],
                "selling_price": stock["sellingPrice"],
                "cheapest_shipping": min(
                    [
                        shipping_info["shipFee"]
                        for shipping_info in stock["shippingInfoList"]
                    ]
                )
                if stock["shippingInfoList"]
                else 0.0,
            }
        )


def update_inventories_for_doba():
    file_path = os.path.join(os.path.dirname(__file__), "data/new_sku_stocks.json")
    with open(file_path, "r") as file:
        new_sku_stocks = json.load(file)

    client.update_inventories_by_seller_sku(
        [
            {
                "sellerSkuNumber": stock["sellerSkuNumber"],
                "availableQuantity": stock["new_stock"],
            }
            for stock in new_sku_stocks
        ]
    )


def update_prices_for_doba():
    file_path = os.path.join(os.path.dirname(__file__), "data/new_sku_stocks.json")

    with open(file_path, "r") as file:
        stocks = json.load(file)

    for stock in stocks:
        stock["calculated_price"] = (
            (stock["selling_price"] + stock["cheapest_shipping"]) * 1.2 * 1.35
        )

    client.update_price_by_seller_sku(
        [
            {
                "sellerSkuNumber": stock["sellerSkuNumber"],
                "price": stock["calculated_price"],
            }
            for stock in stocks
        ]
    )


def do_fox_markup():
    fox_listings = filter_fox_listings()

    updates = []
    for listing in fox_listings:
        current_price = listing["price"]

        if not current_price:
            continue

        new_price = current_price * 1.03
        updates.append(
            {
                "sellerSkuNumber": listing["sellerSkuNumber"],
                "price": new_price,
            }
        )

    with open("data/fox_price_updates.json", "w") as file:
        json.dump(updates, file)

def push_fox():
    
    with open("data/fox_price_updates.json", "r") as file:
        updates = json.load(file)

    client.update_price_by_seller_sku(updates)




def main():
    print("===================================")
    print("MICHAELS STOCK UPDATE SCRIPT")
    print("===================================")
    print("\n")

    try:

        client.test_auth()

        data_dir = os.path.join(os.path.dirname(__file__), "data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        print("Pulling down listings...")
        pulldown_listings()

        listings = filter_doba_listings()


        updates = []
        for listing in listings:
            item_no = listing["sellerSkuNumber"].split("-")[-1]

            product_key = f"product:{item_no}"
            product_data = doba_redis.hgetall(product_key)
            product_data = {k.decode(): v.decode() for k, v in product_data.items()}

            stock = 0

            if "stock" in product_data:
                stock = product_data["stock"]

            updates.append(
                {
                    "sellerSkuNumber": listing["sellerSkuNumber"],
                    "availableQuantity": stock,
                }
            )

            # Debug lines for inspecting specific doba items

            if listing["sellerSkuNumber"] == "DB-Tan-D0102HXJ80T":
                print(updates[-1]["availableQuantity"])
                print("hello")

        client.update_inventories_by_seller_sku(updates=updates)

    except Exception as e:
        print(
            "\n\nEncountered unexpected error. Please contact a developer for assistance with the error information below:\n"
        )
        print(e)


if __name__ == "__main__":
    main()
    
    # pulldown_listings()

    # listings_path = os.path.join(os.path.dirname(__file__), "data/listings.json")
    # with open(listings_path, "r") as file:
    #     json_dict = json.load(file)

    # for listing in json_dict["listings"]:
    #     if listing["sellerSkuNumber"] == "DB-Tan-D0102HXJ80T":
    #         print("found it")
