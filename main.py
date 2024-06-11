
import requests
from michaels.client import MichaelsClient
import json
import os
import os
import urllib3

urllib3.disable_warnings()

client = MichaelsClient('https://www.michaels.com/api/mkp/v1', 'eyJhbGciOiJSUzUxMiJ9.eyJqdGkiOiI1NWY1MDc0MmYyNjg0NzI5YmI1ZWUzMmZjYjgxZTMyZSIsIl9zZWxsZXJTdG9yZUlkIjoiMTQ3OTY3NDE3MDM5MzA2NzUyIiwiX2NyZWF0ZVRpbWUiOiIxNzE3MDkyMzcwNjQyIiwiX2V4cGlyZVRpbWUiOiIxNzI0OTA3NTk5MDAwIiwiaXNzIjoibWRhLWFwaSIsInN1YiI6IjE0Nzk2NzQxNzAzOTMwNjc1MiIsImlhdCI6MTcxNzA5MjM3MCwiZXhwIjoxNzI0OTA3NTk5LCJhdWQiOiJhcGlrZXkifQ.VGuH1zWBTHO-RIBzoMtOfnOIMY507_zg1J649u2ThjRhfJo7z4RVd5F6fxSw87o9hj8ndjU_Az4RoM74FzBDuZ1kcZwk1aAEH0rpziYay_19OIuj9395GDWyju6LsTDWy4D3m6YIncbw6HxS9SUXMrioyzfMLtInspNBO9QTNNVj-HuLcfFwAM7gEZTdDqtT0W1dpdBXN26Fn0xCIElcOshqSp96idVKwy3740J9mxXnnfr5b505EvrzKwFUEFV0jT8WaV_yW5l64n7o6XHr6uY7RUpGbg_hJOI9MUA7X115z-5Hd5bEyubFbbD3fy22v3emH_c2XBbTxW8H0zhcCQ')


def pulldown_listings():

    listings = client.get_all_listings()

    json_dict = {'listings': listings}

    file_path = os.path.join(os.path.dirname(__file__), 'data/listings.json')
    with open(file_path, 'w') as file:
        json.dump(json_dict, file)



def filter_doba_listings():

    listings_path = os.path.join(os.path.dirname(__file__), 'data/listings.json')
    with open(listings_path, 'r') as file:
        json_dict = json.load(file)
    
    doba_listings = [listing for listing in json_dict['listings'] if listing['sellerSkuNumber'][:2] == 'Do' or listing['sellerSkuNumber'][:2] == 'DB']

    return doba_listings

def pull_doba_stocks():

    doba_listings = filter_doba_listings()

    stocks = []

    for i in range(0, len(doba_listings), 100):

        params = {
            'itemNos': ','.join([listing['sellerSkuNumber'].split('-')[-1] for listing in doba_listings[i:min(i+100, len(doba_listings))]])
        }

        response = requests.get('https://157.230.2.9/ecgautomation/api/doba/product-info', params=params, verify=False)

        if not response.ok:
            response.raise_for_status()
        else:
            stocks.extend(response.json()['data'])

    output_path = os.path.join(os.path.dirname(__file__), 'data/stocks.json')
    with open(output_path, 'w') as file:
        json.dump(stocks, file)

def generate_new_sku_stocks():

    stocks_path = os.path.join(os.path.dirname(__file__), 'data/stocks.json')
    with open(stocks_path, 'r') as file:
        stocks = json.load(file)

    listings_path = os.path.join(os.path.dirname(__file__), 'data/listings.json')
    with open(listings_path, 'r') as file:
        listings = json.load(file)

    listings_lookup_dict = {listing['sellerSkuNumber'].split('-')[-1]: listing for listing in listings['listings']}

    new_sku_stocks = []

    for stock in stocks:
        new_sku_stocks.append({
            'sellerSkuNumber': listings_lookup_dict[stock['itemNo']]['sellerSkuNumber'],
            'new_stock': stock['stock']
        })

    output_path = os.path.join(os.path.dirname(__file__), 'data/new_sku_stocks.json')
    with open(output_path, 'w') as file:
        json.dump(new_sku_stocks, file)

def update_inventories_for_doba():

    file_path = os.path.join(os.path.dirname(__file__), 'data/new_sku_stocks.json')
    with open(file_path, 'r') as file:
        new_sku_stocks = json.load(file)

    client.update_inventories_by_seller_sku([{'sellerSkuNumber': stock['sellerSkuNumber'], 'availableQuantity': stock['new_stock']} for stock in new_sku_stocks])


def main():

    print("===================================")
    print("MICHAELS STOCK UPDATE SCRIPT")
    print("===================================")
    print("\n")

    try:

        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        print("Pulling down listings...")
        pulldown_listings()

        print("Pulling down doba stocks from production server...")
        pull_doba_stocks()

        print("Generating new sku stocks...")
        generate_new_sku_stocks()

        print("Performing inventory updates via Michaels API...")
        update_inventories_for_doba()

        print("Performing file cleanup...")
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        for file_name in os.listdir(data_dir):
            if file_name.endswith('.json'):
                file_path = os.path.join(data_dir, file_name)
                os.remove(file_path)

        print("\n\nUpdate finished! You may now close this terminal window.")
        input("\n\nPress ENTER key to close window...")

    except Exception as e:
        print("\n\nEncountered unexpected error. Please contact a developer for assistance with the error information below:\n")
        print(e)

        input("\n\nPress ENTER key to close window...")


if __name__ == '__main__':
    main()