import os
import json
import pandas as pd
from functools import lru_cache
from jugaad_data.nse import NSELive
import time
    
def load_users(path: str) -> list:
    json_list = [f for f in os.listdir(path) if f.endswith('.json')]
    return [f.replace('.json', '') for f in json_list]

def load_data(username: str, path: str) -> dict:
    with open(path + username + ".json", "r") as f:
        data = json.load(f)
    return data['data']

def save_data(data: dict, selected_user: str, path: str):
    with open(path + selected_user + ".json", "w") as f:
        json.dump({"data": data}, f)
        
def convert_to_df(data: dict):
    return pd.DataFrame(data)

def get_prices_batch(symbols: list[str]) -> dict:
    """
    Fetch current prices for a list of symbols in a single batch using yf.download.
    Returns a dict of symbol -> price.
    """
    # yf_symbols = [s.strip().upper() + ".NS" for s in symbols]
    # price_df = yf.download(tickers=yf_symbols, period="1d", interval="1d", group_by='ticker', progress=False)

    prices = {}
    # for original_sym, yf_sym in zip(symbols, yf_symbols):
    #     try:
    #         if len(symbols) == 1:
    #             # yf returns single-column DF if only one ticker
    #             close_price = price_df['Close'].iloc[-1]
    #         else:
    #             close_price = price_df[yf_sym]['Close'].iloc[-1]
    #         prices[original_sym] = round(float(close_price), 2)
    #     except Exception as e:
    #         print(f"Error fetching price for {original_sym}: {e}")
    #         prices[original_sym] = None
    # return prices
    n = NSELive()
    for sym in symbols:
        time.sleep(0.3)
        try:
            info = n.stock_quote(sym).get('priceInfo', None)
            if info is not None:
                last_price = info.get('lastPrice', None)
                if last_price is not None:
                    prices[sym] = float(last_price)
                    print(f"Successfully fetched latest price for {sym}")
        except Exception as e:
            print(f"Error fetching price for {sym}: {e}")
            prices[sym] = None
    return prices

def highlight_pl(val):
    color = 'green' if val > 0 else 'red' if val < 0 else 'black'
    return f'color: {color}'


def process_uploaded(uploaded_data):
    pass