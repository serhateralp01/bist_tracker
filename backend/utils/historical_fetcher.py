import yfinance as yf
import pandas as pd
from datetime import date, timedelta, datetime
from typing import List, Dict, Optional, Any
import numpy as np
from sqlalchemy.orm import Session
from backend import models

def get_historical_data(symbols: List[str], start_date: date, end_date: date) -> pd.DataFrame:
    """
    Fetches historical closing prices for a list of symbols over a given date range
    in a single, efficient API call.

    Returns a pandas DataFrame with dates as the index and symbols as columns.
    Missing data for non-trading days is forward-filled.
    """
    if not symbols:
        return pd.DataFrame()
        
    try:
        # Append .IS for BIST stocks if not already present
        formatted_symbols = []
        for s in symbols:
            if s.upper() != 'EURTRY=X' and not s.upper().endswith('.IS'):
                formatted_symbols.append(f"{s}.IS")
            else:
                formatted_symbols.append(s)

        # yfinance expects symbols separated by spaces
        ticker_string = " ".join(formatted_symbols)
        
        # Fetch data
        data = yf.download(ticker_string, start=start_date, end=end_date, progress=False, auto_adjust=True)
        
        if data.empty:
            return pd.DataFrame()

        # We only need the closing prices
        close_prices = data['Close']
        
        # If only one symbol is fetched, it's a Series, convert it to a DataFrame
        if isinstance(close_prices, pd.Series):
            close_prices = close_prices.to_frame(name=formatted_symbols[0])

        # Forward-fill missing values for weekends/holidays
        return close_prices.ffill()

    except Exception as e:
        print(f"Error fetching historical bulk data: {e}")
        return pd.DataFrame()

def get_stock_historical_chart(symbol: str, period: str = "1y") -> Dict[str, Any]:
    """
    Get detailed historical data for a single stock with technical indicators.
    """
    try:
        # Format symbol and create ticker
        formatted_symbol = f"{symbol}.IS" if not symbol.endswith('.IS') else symbol
        ticker = yf.Ticker(formatted_symbol)
        
        # Get historical data
        hist = ticker.history(period=period)
        if hist.empty:
            return {"error": f"No data found for {symbol}"}
        
        # Convert to timezone-naive for JSON serialization
        hist.index = hist.index.tz_localize(None)
        
        # Calculate technical indicators
        hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
        hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
        hist['Daily_Return'] = hist['Close'].pct_change()
        hist['Volatility'] = hist['Daily_Return'].rolling(window=20).std() * np.sqrt(252)

        # Format data for JSON response
        chart_data = []
        for date_idx, row in hist.iterrows():
            chart_data.append({
                'date': date_idx.strftime('%Y-%m-%d'),
                'open': round(float(row['Open']), 2),
                'high': round(float(row['High']), 2),
                'low': round(float(row['Low']), 2),
                'close': round(float(row['Close']), 2),
                'volume': int(row['Volume']) if not pd.isna(row['Volume']) else 0,
                'sma_20': round(float(row['SMA_20']), 2) if not pd.isna(row['SMA_20']) else None,
                'sma_50': round(float(row['SMA_50']), 2) if not pd.isna(row['SMA_50']) else None,
                'daily_return': round(float(row['Daily_Return']) * 100, 2) if not pd.isna(row['Daily_Return']) else None,
                'volatility': round(float(row['Volatility']) * 100, 2) if not pd.isna(row['Volatility']) else None
            })
        
        # Calculate summary statistics
        latest_price = float(hist['Close'].iloc[-1])
        period_start_price = float(hist['Close'].iloc[0])
        total_return = ((latest_price - period_start_price) / period_start_price) * 100
        
        max_price = float(hist['Close'].max())
        min_price = float(hist['Close'].min())
        avg_volume = int(hist['Volume'].mean()) if not hist['Volume'].empty else 0
        
        return {
            'symbol': symbol,
            'period': period,
            'data': chart_data,
            'summary': {
                'latest_price': round(latest_price, 2),
                'period_return': round(total_return, 2),
                'max_price': round(max_price, 2),
                'min_price': round(min_price, 2),
                'avg_volume': avg_volume,
                'data_points': len(chart_data)
            }
        }
        
    except Exception as e:
        return {"error": f"Error fetching chart data for {symbol}: {str(e)}"}

def get_portfolio_timeline_data(symbols: List[str], start_date: date, end_date: date) -> Dict[str, Any]:
    """
    Generates a timeline of portfolio value and individual stock performance
    """
    try:
        hist_data = get_historical_data(symbols, start_date, end_date)
        if hist_data.empty:
            return {"error": "No historical data available for timeline"}
        
        # Calculate daily returns for each stock
        returns = hist_data.pct_change().fillna(0)
        
        # Calculate cumulative returns
        cumulative_returns = (1 + returns).cumprod()
        
        # Prepare data for response
        timeline_data = {
            'dates': [d.strftime('%Y-%m-%d') for d in cumulative_returns.index],
            'portfolio_performance': [], # This can be enhanced with holdings data
            'symbols': {}
        }
        
        for symbol in symbols:
            symbol_col = f"{symbol}.IS"
            if symbol_col in cumulative_returns.columns:
                timeline_data['symbols'][symbol] = {
                    'daily_returns': returns[symbol_col].round(4).tolist(),
                    'cumulative_performance': (cumulative_returns[symbol_col] - 1).round(4).tolist()
                }

        return {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            **timeline_data
        }
    except Exception as e:
        return {"error": f"Error calculating portfolio timeline: {str(e)}"}

def get_market_comparison_data(db: Session, symbol: str, period: str = "1y") -> Dict[str, Any]:
    """
    Compare stock performance against BIST indices
    """
    try:
        # Get stock data using ticker
        formatted_symbol = f"{symbol}.IS" if not symbol.endswith('.IS') else symbol
        ticker = yf.Ticker(formatted_symbol)
        stock_data = ticker.history(period=period)
        
        if stock_data.empty:
            return {"error": f"No data found for {symbol}"}
        
        # Convert to timezone-naive
        stock_data.index = stock_data.index.tz_localize(None)
        
        # Get BIST 100 and BIST 30 data
        indices = {
            "BIST 100": "XU100.IS",
            "BIST 30": "XU030.IS"
        }
        
        comparison_data = {
            "symbol": symbol,
            "period": period,
            "stock_data": [],
            "indices": {}
        }
        
        # Format stock data
        for date, row in stock_data.iterrows():
            comparison_data["stock_data"].append({
                "date": date.strftime("%Y-%m-%d"),
                "close": round(float(row["Close"]), 2),
                "change_pct": 0  # Will calculate below
            })
        
        # Calculate stock percentage changes
        if len(comparison_data["stock_data"]) > 1:
            base_price = comparison_data["stock_data"][0]["close"]
            for data_point in comparison_data["stock_data"]:
                data_point["change_pct"] = round(((data_point["close"] - base_price) / base_price) * 100, 2)
        
        # Get index data
        for index_name, index_symbol in indices.items():
            try:
                index_ticker = yf.Ticker(index_symbol)
                index_data = index_ticker.history(period=period)
                if not index_data.empty:
                    # Convert to timezone-naive
                    index_data.index = index_data.index.tz_localize(None)
                    
                    index_points = []
                    for date, row in index_data.iterrows():
                        index_points.append({
                            "date": date.strftime("%Y-%m-%d"),
                            "close": round(float(row["Close"]), 2),
                            "change_pct": 0
                        })
                    
                    # Calculate index percentage changes
                    if len(index_points) > 1:
                        base_price = index_points[0]["close"]
                        for point in index_points:
                            point["change_pct"] = round(((point["close"] - base_price) / base_price) * 100, 2)
                    
                    comparison_data["indices"][index_name] = index_points
            except Exception as e:
                print(f"Error fetching {index_name}: {e}")
                continue
        
        return comparison_data
        
    except Exception as e:
        return {"error": f"Error fetching comparison data: {str(e)}"}

def get_risk_metrics(db: Session, period: str = "1y") -> Dict[str, Any]:
    """
    Calculate various risk metrics for portfolio stocks
    """
    try:
        # Get symbols from database transactions
        transactions = db.query(models.Transaction).all()
        symbols = list(set(tx.symbol for tx in transactions if tx.symbol))
        
        if not symbols:
            return {"error": "No stocks found in portfolio"}
        
        # Get historical data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=365 if period == "1y" else 180)
        
        hist_data = get_historical_data(symbols, start_date, end_date)
        if hist_data.empty:
            return {"error": "No historical data available"}
        
        # Calculate daily returns
        returns = hist_data.pct_change().dropna()
        
        risk_metrics = {}
        for symbol in symbols:
            symbol_col = f"{symbol}.IS" if not symbol.endswith('.IS') else symbol
            if symbol_col in returns.columns:
                symbol_returns = returns[symbol_col].dropna()
                
                if len(symbol_returns) > 20:  # Ensure sufficient data
                    # Calculate metrics
                    volatility = float(symbol_returns.std() * np.sqrt(252) * 100)  # Annualized volatility
                    annualized_return = float(symbol_returns.mean() * 252 * 100)  # Annualized return
                    
                    # Sharpe ratio (assuming 0% risk-free rate)
                    sharpe_ratio = float(annualized_return / volatility) if volatility > 0 else 0
                    
                    # Maximum drawdown
                    cumulative = (1 + symbol_returns).cumprod()
                    peak = cumulative.expanding().max()
                    drawdown = (cumulative / peak - 1) * 100
                    max_drawdown = float(drawdown.min())
                    
                    # Value at Risk (95% confidence)
                    var_95 = float(np.percentile(symbol_returns * 100, 5))
                    
                    risk_metrics[symbol] = {
                        'volatility': volatility,
                        'annualized_return': annualized_return,
                        'sharpe_ratio': sharpe_ratio,
                        'max_drawdown': max_drawdown,
                        'var_95': var_95
                    }
        
        return {
            'risk_metrics': risk_metrics
        }
        
    except Exception as e:
        return {"error": f"Error calculating risk metrics: {str(e)}"} 