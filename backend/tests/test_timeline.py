
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from backend.utils.historical_fetcher import get_portfolio_timeline_data
from backend.models import Transaction

@pytest.fixture
def mock_db():
    db = MagicMock()
    return db

@patch('backend.utils.historical_fetcher.get_current_holdings')
@patch('backend.utils.historical_fetcher.get_user_performance_since_purchase')
@patch('backend.utils.historical_fetcher.get_historical_data')
def test_get_portfolio_timeline_data(mock_hist_data, mock_user_perf, mock_holdings, mock_db):
    import pandas as pd
    import numpy as np

    # Mock holdings
    mock_holdings.return_value = ['THYAO']

    # Mock user performance
    mock_user_perf.return_value = {
        'average_purchase_price': 100.0,
        'first_purchase_date': date(2023, 1, 1)
    }

    # Mock historical data
    dates = pd.date_range(start='2023-01-01', periods=5)
    df = pd.DataFrame({
        'THYAO.IS': [100.0, 102.0, 105.0, 103.0, 106.0]
    }, index=dates)
    mock_hist_data.return_value = df

    # Mock transactions
    mock_tx = MagicMock()
    mock_tx.symbol = 'THYAO'
    mock_tx.quantity = 10
    mock_tx.type = 'buy'
    mock_tx.date = date(2023, 1, 1)

    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_tx]

    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 5)

    result = get_portfolio_timeline_data(mock_db, start_date, end_date)

    assert 'dates' in result
    assert 'portfolio_performance' in result
    assert len(result['dates']) == 5
    assert len(result['portfolio_performance']) == 5
    # Value = 10 qty * price
    assert result['portfolio_performance'][0] == 1000.0
    assert result['portfolio_performance'][-1] == 1060.0
