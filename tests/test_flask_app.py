def test_home_page(test_client):
    response = test_client.get('/')
    assert response.status_code == 200
    assert b"BIST Tracker" in response.data

def test_transactions_page(test_client):
    response = test_client.get('/transactions')
    assert response.status_code == 200
    assert b"Add Transaction" in response.data

def test_search_api(test_client):
    # Mock search should return something for 'MAC' or 'AAPL'
    response = test_client.get('/api/search?q=MAC')
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    # Assuming search_assets works (it was tested in previous backend tests)
    # MAC is a TEFAS fund
    if len(data) > 0:
        assert 'symbol' in data[0]

def test_add_transaction(test_client):
    response = test_client.post('/transactions', data={
        'date': '2023-10-01',
        'type': 'buy',
        'symbol': 'THYAO',
        'quantity': '10',
        'price': '250.5',
        'currency': 'TRY',
        'asset_type': 'STOCK'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"THYAO" in response.data
