# services/financial_data_service.py
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.fundamentaldata import FundamentalData
from ..utils.config import ALPHA_VANTAGE_API_KEY
import time

# Note: The free Alpha Vantage API has limitations (e.g., 5 calls per minute, 500 per day).
# Proper error handling and potentially rate limiting or caching should be considered for a robust app.

def get_company_overview(symbol: str):
    """
    Fetches company overview data from Alpha Vantage.

    Args:
        symbol (str): The company stock symbol (e.g., "AAPL" for Apple).

    Returns:
        dict: A dictionary containing company overview data, or None if an error occurs or API key is missing.
    """
    if not ALPHA_VANTAGE_API_KEY:
        print("Error: ALPHA_VANTAGE_API_KEY is not set.")
        return None
    
    try:
        fd = FundamentalData(key=ALPHA_VANTAGE_API_KEY, output_format='json')
        # The FundamentalData class methods for company overview, earnings, etc.,
        # are not explicitly listed in some older docs of the wrapper,
        # but the API itself supports OVERVIEW, EARNINGS, etc.
        # We might need to make a direct request if the wrapper is outdated or limited.
        # Let's try using the base _call_api_on_func directly if a dedicated method isn't obvious.
        
        # The API endpoint for Company Overview is 'OVERVIEW'
        # Making a more direct call if `get_company_overview` is not a method of `FundamentalData`
        data, _ = fd.get_company_overview(symbol=symbol) #This method should exist with recent versions
        return data
    except Exception as e:
        # Check if it's a ValueError from the library for API limits
        if "Our standard API call frequency is 5 calls per minute and 500 calls per day." in str(e):
            print(f"Alpha Vantage API limit likely reached for symbol {symbol}: {e}")
        else:
            print(f"Error fetching company overview for {symbol} from Alpha Vantage: {e}")
        return None

def get_daily_stock_prices(symbol: str, outputsize: str = "compact"):
    """
    Fetches daily time series stock data (open, high, low, close, volume) from Alpha Vantage.

    Args:
        symbol (str): The company stock symbol.
        outputsize (str, optional): "compact" for last 100 days, "full" for full history. Defaults to "compact".

    Returns:
        dict: A dictionary containing daily time series data, or None if an error occurs or API key is missing.
              The data is usually keyed by date.
    """
    if not ALPHA_VANTAGE_API_KEY:
        print("Error: ALPHA_VANTAGE_API_KEY is not set.")
        return None
            
    try:
        ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='json')
        data, meta_data = ts.get_daily(symbol=symbol, outputsize=outputsize)
        # data will be like: {'2023-10-20': {'1. open': '172.5800', ...}, ...}
        # meta_data will be like: {'1. Information': 'Daily Prices...', ...}
        return {"data": data, "meta_data": meta_data}
    except Exception as e:
        if "Our standard API call frequency is 5 calls per minute and 500 calls per day." in str(e):
            print(f"Alpha Vantage API limit likely reached for symbol {symbol}: {e}")
        else:
            print(f"Error fetching daily stock prices for {symbol} from Alpha Vantage: {e}")
        return None

# Add more functions as needed, e.g., for earnings, income statement, balance sheet.
# Example: get_earnings(symbol: str)

if __name__ == '__main__':
    # Example Usage:
    # To run this test, navigate to the 'financial_research_assistant' directory
    # and run: python -m services.financial_data_service
    # Ensure ALPHA_VANTAGE_API_KEY is set.

    print("\n--- FinancialDataService Test ---")
    if not ALPHA_VANTAGE_API_KEY:
        print("Skipping test as ALPHA_VANTAGE_API_KEY is not set.")
    else:
        sample_symbol = "IBM" # Using IBM as it's a common example for Alpha Vantage
        
        print(f"\nFetching company overview for {sample_symbol}...")
        overview = get_company_overview(sample_symbol)
        if overview:
            print(f"Company Name: {overview.get('Name')}")
            print(f"Description (first 100 chars): {overview.get('Description', '')[:100]}...")
            # print(f"Full Overview: {overview}")
        else:
            print(f"Could not fetch overview for {sample_symbol}.")

        # Wait a bit due to API rate limits if making multiple calls
        print("\nWaiting for a few seconds due to API rate limits before next call...")
        time.sleep(15) # Alpha Vantage free tier is very restrictive (5 calls/min)

        print(f"\nFetching daily stock prices for {sample_symbol} (compact)...")
        stock_data = get_daily_stock_prices(sample_symbol, outputsize="compact")
        if stock_data and stock_data.get("data"):
            print(f"Meta Data: {stock_data.get('meta_data')}")
            # Print data for the most recent day available (first key in dict usually)
            first_day = next(iter(stock_data['data'])) if stock_data['data'] else None
            if first_day:
                print(f"Data for {first_day}: {stock_data['data'][first_day]}")
            else:
                print("No daily data found in response.")
        else:
            print(f"Could not fetch stock prices for {sample_symbol}.")
        
        print("--- Test End ---")
