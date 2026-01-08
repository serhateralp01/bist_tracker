import pytest
from app.services.forecast import generate_forecast
from datetime import datetime, timedelta
import pandas as pd
from unittest.mock import patch, MagicMock

@patch('app.services.forecast.get_historical_data')
def test_generate_forecast_success(mock_get_historical_data):
    # Mock historical data
    dates = pd.date_range(end=datetime.now(), periods=100)
    # Create a linear trend
    values = [10 + i * 0.1 for i in range(100)]

    mock_df = pd.DataFrame({
        'TEST.IS': values
    }, index=dates)

    mock_get_historical_data.return_value = mock_df

    result = generate_forecast('TEST', periods=10)

    assert "error" not in result
    assert result['symbol'] == 'TEST'
    assert len(result['history']['values']) == 100
    assert len(result['forecast']['values']) == 10

    # Check if forecast continues the trend roughly
    last_hist = result['history']['values'][-1]
    first_forecast = result['forecast']['values'][0]
    assert first_forecast > last_hist # Should be increasing

@patch('app.services.forecast.get_historical_data')
def test_generate_forecast_not_enough_data(mock_get_historical_data):
    # Mock historical data with too few points
    dates = pd.date_range(end=datetime.now(), periods=10)
    values = [10] * 10

    mock_df = pd.DataFrame({
        'TEST.IS': values
    }, index=dates)

    mock_get_historical_data.return_value = mock_df

    result = generate_forecast('TEST')

    assert "error" in result
    assert "Not enough data" in result["error"]

@patch('app.services.forecast.get_historical_data')
def test_generate_forecast_no_data(mock_get_historical_data):
    mock_get_historical_data.return_value = pd.DataFrame()

    result = generate_forecast('INVALID')

    assert "error" in result
    assert "No data found" in result["error"]
