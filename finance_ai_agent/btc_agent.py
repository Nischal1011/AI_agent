import requests
from datetime import datetime
from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def store_btc_price(price: float):
    """
    Store Bitcoin price in Supabase
    Args:
        price (float): Current Bitcoin price
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        data = {
            "price": price,
        }
        print(f"Attempting to insert data: {data}")
        result = supabase.table("btc_price").insert(data).execute()
        print(f"Supabase response: {result}")
        return True
    except Exception as e:
        print(f"Error storing price in Supabase: {str(e)}")
        print(f"Error type: {type(e)}")
        print(f"Error details: {e.__dict__}")  # This will show us more error details
        # Print environment variables (but mask the key)
        supabase_url = os.getenv("SUPABASE_URL", "Not found")
        supabase_key = os.getenv("SUPABASE_KEY", "Not found")
        if supabase_key != "Not found":
            supabase_key = supabase_key[:6] + "..." + supabase_key[-4:]
        print(f"SUPABASE_URL: {supabase_url}")
        print(f"SUPABASE_KEY: {supabase_key}")
        return False

def get_btc_price():
    """
    Fetch the current Bitcoin price in USD using CoinGecko API
    Returns: float or None if request fails
    """
    try:
        # CoinGecko API endpoint for Bitcoin price in USD
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin",
            "vs_currencies": "usd"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for bad status codes
        
        data = response.json()
        btc_price = data["bitcoin"]["usd"]
        # Store price in Supabase
        if store_btc_price(btc_price):
            print("Price stored successfully in Supabase")
        return btc_price
        
    except (requests.RequestException, KeyError) as e:
        print(f"Error fetching Bitcoin price: {e}")
        return None

# Example usage
if __name__ == "__main__":
    price = get_btc_price()
    if price:
        print(f"Current Bitcoin Price: ${price:,.2f} USD")
