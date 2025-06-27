import yfinance as yf
import pandas as pd
from datetime import date, timedelta, datetime
from typing import List, Dict, Optional, Any
import numpy as np

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
    Get detailed historical chart data for a single stock
    
    Args:
        symbol: Stock symbol (e.g., 'SISE')
        period: Time period ('1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
    
    Returns:
        Dictionary with OHLCV data and technical indicators
    """
    try:
        # Format symbol
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
        
        # Calculate daily returns
        hist['Daily_Return'] = hist['Close'].pct_change()
        
        # Calculate volatility (20-day rolling)
        hist['Volatility'] = hist['Daily_Return'].rolling(window=20).std() * np.sqrt(252)
        
        # Prepare data for response
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
    Get comprehensive portfolio timeline data with individual stock performance
    """
    try:
        if not symbols:
            return {"error": "No symbols provided"}
        
        # Get historical data for all symbols
        hist_data = get_historical_data(symbols, start_date, end_date)
        if hist_data.empty:
            return {"error": "No historical data available"}
        
        # Calculate returns for each symbol
        returns_data = {}
        for symbol in symbols:
            symbol_col = f"{symbol}.IS" if not symbol.endswith('.IS') else symbol
            if symbol_col in hist_data.columns:
                prices = hist_data[symbol_col].dropna()
                if len(prices) > 1:
                    daily_returns = prices.pct_change().dropna()
                    cumulative_returns = (1 + daily_returns).cumprod() - 1
                    
                    returns_data[symbol] = {
                        'daily_returns': daily_returns.tolist(),
                        'cumulative_returns': (cumulative_returns * 100).tolist(),
                        'dates': [d.strftime('%Y-%m-%d') for d in cumulative_returns.index],
                        'volatility': float(daily_returns.std() * np.sqrt(252) * 100),
                        'total_return': float(cumulative_returns.iloc[-1] * 100) if len(cumulative_returns) > 0 else 0
                    }
        
        return {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'symbols': returns_data
        }
        
    except Exception as e:
        return {"error": f"Error calculating portfolio timeline: {str(e)}"}

def get_market_comparison_data(symbol: str, comparison_symbols: List[str] = None, period: str = "1y") -> Dict[str, Any]:
    """
    Compare a stock's performance against market indices and other stocks
    
    Args:
        symbol: Primary stock symbol
        comparison_symbols: List of symbols to compare against (default: BIST100, BIST30)
        period: Time period for comparison
    """
    try:
        # Default comparison symbols
        if comparison_symbols is None:
            comparison_symbols = ['XU100', 'XU030']  # BIST 100 and BIST 30
        
        # Combine all symbols
        all_symbols = [symbol] + comparison_symbols
        
        # Get historical data
        end_date = datetime.now().date()
        if period == "1mo":
            start_date = end_date - timedelta(days=30)
        elif period == "3mo":
            start_date = end_date - timedelta(days=90)
        elif period == "6mo":
            start_date = end_date - timedelta(days=180)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        elif period == "2y":
            start_date = end_date - timedelta(days=730)
        else:
            start_date = end_date - timedelta(days=365)
        
        hist_data = get_historical_data(all_symbols, start_date, end_date)
        if hist_data.empty:
            return {"error": "No historical data available"}
        
        # Calculate normalized performance (percentage change from start)
        comparison_data = {}
        for sym in all_symbols:
            sym_col = f"{sym}.IS" if not sym.endswith('.IS') else sym
            if sym_col in hist_data.columns:
                prices = hist_data[sym_col].dropna()
                if len(prices) > 1:
                    # Normalize to start at 0%
                    normalized = ((prices / prices.iloc[0]) - 1) * 100
                    comparison_data[sym] = {
                        'dates': [d.strftime('%Y-%m-%d') for d in normalized.index],
                        'performance': normalized.round(2).tolist(),
                        'latest_return': float(normalized.iloc[-1]) if len(normalized) > 0 else 0
                    }
        
        return {
            'primary_symbol': symbol,
            'comparison_symbols': comparison_symbols,
            'period': period,
            'data': comparison_data
        }
        
    except Exception as e:
        return {"error": f"Error generating market comparison: {str(e)}"}

def get_correlation_analysis(symbols: List[str], period: str = "1y") -> Dict[str, Any]:
    """
    Calculate correlation matrix between stocks in portfolio
    """
    try:
        if len(symbols) < 2:
            return {"error": "Need at least 2 symbols for correlation analysis"}
        
        # Get historical data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=365 if period == "1y" else 180)
        
        hist_data = get_historical_data(symbols, start_date, end_date)
        if hist_data.empty:
            return {"error": "No historical data available"}
        
        # Calculate daily returns
        returns = hist_data.pct_change().dropna()
        
        # Calculate correlation matrix
        correlation_matrix = returns.corr()
        
        # Convert to dictionary format
        correlation_data = {}
        for i, symbol1 in enumerate(symbols):
            symbol1_col = f"{symbol1}.IS" if not symbol1.endswith('.IS') else symbol1
            if symbol1_col in correlation_matrix.columns:
                correlation_data[symbol1] = {}
                for j, symbol2 in enumerate(symbols):
                    symbol2_col = f"{symbol2}.IS" if not symbol2.endswith('.IS') else symbol2
                    if symbol2_col in correlation_matrix.columns:
                        corr_value = correlation_matrix.loc[symbol1_col, symbol2_col]
                        correlation_data[symbol1][symbol2] = round(float(corr_value), 3) if not pd.isna(corr_value) else 0
        
        return {
            'symbols': symbols,
            'period': period,
            'correlation_matrix': correlation_data
        }
        
    except Exception as e:
        return {"error": f"Error calculating correlations: {str(e)}"}

def get_risk_metrics(symbols: List[str], period: str = "1y") -> Dict[str, Any]:
    """
    Calculate various risk metrics for portfolio stocks
    """
    try:
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
                    volatility = symbol_returns.std() * np.sqrt(252) * 100  # Annualized volatility
                    avg_return = symbol_returns.mean() * 252 * 100  # Annualized return
                    
                    # Sharpe ratio (assuming 0% risk-free rate)
                    sharpe_ratio = avg_return / volatility if volatility > 0 else 0
                    
                    # Maximum drawdown
                    cum_returns = (1 + symbol_returns).cumprod()
                    running_max = cum_returns.expanding().max()
                    drawdown = (cum_returns - running_max) / running_max
                    max_drawdown = drawdown.min() * 100
                    
                    # Value at Risk (95% confidence)
                    var_95 = np.percentile(symbol_returns, 5) * 100
                    
                    risk_metrics[symbol] = {
                        'volatility': round(volatility, 2),
                        'annualized_return': round(avg_return, 2),
                        'sharpe_ratio': round(sharpe_ratio, 3),
                        'max_drawdown': round(max_drawdown, 2),
                        'var_95': round(var_95, 2)
                    }
        
        return {
            'symbols': symbols,
            'period': period,
            'risk_metrics': risk_metrics
        }
        
    except Exception as e:
        return {"error": f"Error calculating risk metrics: {str(e)}"} 