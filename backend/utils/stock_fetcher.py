import yfinance as yf

def get_latest_price(symbol: str) -> float:
    try:
        ticker = yf.Ticker(symbol + ".IS")
        hist = ticker.history(period="1d")
        if hist.empty:
            return None
        return round(hist['Close'].iloc[-1], 2)
    except Exception:
        return None