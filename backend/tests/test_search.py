import pytest
from backend.utils.search_service import search_assets

def test_search_fund():
    # Searching for a known fund code
    results = search_assets("MAC")
    # Should find at least the TEFAS assumption match
    assert any(r['symbol'] == 'MAC' and r['type'] == 'FUND' for r in results)

def test_search_stock_us():
    # Searching for Apple
    results = search_assets("AAPL")
    # Should find Apple Inc.
    apple = next((r for r in results if r['symbol'] == 'AAPL'), None)
    assert apple is not None
    assert apple['type'] == 'STOCK'
    assert apple['currency'] == 'USD'

def test_search_stock_tr():
    # Searching for Turkish Airlines
    results = search_assets("THYAO")
    # Should find THYAO.IS
    thyao = next((r for r in results if 'THYAO' in r['symbol']), None)
    assert thyao is not None
    assert thyao['currency'] == 'TRY'
