import requests
import yfinance as yf
from typing import List, Dict, Optional

def search_assets(query: str) -> List[Dict]:
    """
    Search for assets (Stocks and Funds).
    """
    results = []

    # 1. Search TEFAS Funds (Mock/Limited search or full list)
    # TEFAS doesn't have a public search API easily accessible without scraping everything.
    # However, we can check if the query matches a known fund code format (3 uppercase letters).
    if len(query) == 3 and query.isalpha():
         results.append({
             "symbol": query.upper(),
             "name": f"TEFAS Fund {query.upper()}", # We don't have the name without fetching list
             "type": "FUND",
             "currency": "TRY",
             "exchange": "TEFAS"
         })

    # 2. Search Yahoo Finance (Stocks)
    try:
        # Use Yahoo Finance auto-complete API
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if 'quotes' in data:
                for item in data['quotes']:
                    # Filter for relevant types
                    quote_type = item.get('quoteType', '')
                    if quote_type not in ['EQUITY', 'ETF', 'MUTUALFUND']:
                        continue

                    symbol = item.get('symbol', '')
                    name = item.get('shortname') or item.get('longname') or symbol
                    exch = item.get('exchange', '')

                    # Determine Currency
                    # Yahoo search result doesn't always give currency directly in this endpoint?
                    # It gives 'score', 'typeDisp', 'isYahooFinance', etc.
                    # We can infer from suffix or exchange.

                    currency = "USD" # Default
                    if symbol.endswith('.IS') or exch == 'IST':
                        currency = "TRY"
                        # Strip .IS for clean display if desired, or keep it.
                        # User wants: "Goog yazınca... seçsin. hangi markette olduguna göre döviz..."
                    elif '.DE' in symbol:
                        currency = "EUR"
                    elif '.L' in symbol:
                        currency = "GBP"

                    # Clean symbol for BIST
                    display_symbol = symbol
                    if symbol.endswith(".IS"):
                        display_symbol = symbol.replace(".IS", "")

                    results.append({
                        "symbol": display_symbol,
                        "name": name,
                        "type": "STOCK", # Simplify to STOCK for now, even if ETF
                        "currency": currency,
                        "exchange": exch,
                        "yahoo_symbol": symbol # Keep the real yahoo symbol for fetching
                    })
    except Exception as e:
        print(f"Error searching YFinance: {e}")

    return results
