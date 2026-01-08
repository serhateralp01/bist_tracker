import pytest
from app.models import Transaction
from datetime import date

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Dashboard" in response.data

def test_portfolio_route_empty(client):
    response = client.get('/portfolio')
    assert response.status_code == 200
    assert b"No holdings found" in response.data

def test_transaction_add_and_portfolio_update(client, app):
    # Add a transaction
    with app.app_context():
        # Using the route to add transaction
        response = client.post('/transactions/add', data={
            'date': '2023-01-01',
            'type': 'buy',
            'symbol': 'THYAO',
            'quantity': 100,
            'price': 150.0,
            'note': 'Test buy'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"Transaction added successfully" in response.data

    # Check portfolio reflects this
    response = client.get('/portfolio')
    assert response.status_code == 200
    assert b"THYAO" in response.data
    assert b"100.0" in response.data

def test_transaction_delete(client, app):
    # Add a transaction first
    with app.app_context():
        response = client.post('/transactions/add', data={
            'date': '2023-01-01',
            'type': 'buy',
            'symbol': 'ASELS',
            'quantity': 50,
            'price': 40.0,
            'note': 'To delete'
        }, follow_redirects=True)

        # Get the ID of the transaction we just added
        # Since it's a test DB, it should be the first one if isolated, but let's check
        from app.models import Transaction
        from app import db
        tx = db.session.query(Transaction).filter_by(symbol='ASELS').first()
        tx_id = tx.id

    # Delete it
    response = client.post(f'/transactions/delete/{tx_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b"Transaction deleted" in response.data

    # Verify it's gone
    with app.app_context():
        tx = db.session.query(Transaction).filter_by(id=tx_id).first()
        assert tx is None
