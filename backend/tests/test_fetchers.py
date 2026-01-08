import pytest
from backend.utils.fund_fetcher import get_fund_price
from backend.utils.stock_fetcher import get_latest_price

# Note: These tests hit external APIs (TEFAS, Yahoo Finance).
# Ideally, we should mock them, but for this task verification, real calls confirm functionality.

def test_fetch_fund_price():
    # MAC is a known fund (Marmara Capital)
    price = get_fund_price("MAC")
    assert price is not None
    assert isinstance(price, float)
    assert price > 0

def test_fetch_stock_price_try():
    # THYAO is Turkish Airlines
    price = get_latest_price("THYAO", asset_type="STOCK", currency="TRY")
    assert price is not None
    assert price > 0

def test_fetch_stock_price_usd():
    # AAPL is Apple
    price = get_latest_price("AAPL", asset_type="STOCK", currency="USD")
    assert price is not None
    assert price > 0

def test_unified_fetcher_fund():
    price = get_latest_price("MAC", asset_type="FUND", currency="TRY")
    assert price is not None
    assert price > 0
