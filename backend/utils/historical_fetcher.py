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

def get_portfolio_timeline_data(db: Session, start_date: date, end_date: date) -> Dict[str, Any]:
    """
    Generates a timeline of portfolio value and individual stock performance
    Only includes stocks currently held in portfolio
    """
    try:
        from backend.utils.portfolio_calculator import get_current_holdings
        
        # Get only currently held stocks
        symbols = get_current_holdings(db)
        if not symbols:
            return {"error": "No stocks currently held in portfolio"}
        
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
    Only includes stocks currently held in portfolio
    """
    try:
        from backend.utils.portfolio_calculator import get_current_holdings
        
        # Get only currently held stocks
        symbols = get_current_holdings(db)
        if not symbols:
            return {"error": "No stocks currently held in portfolio"}
        
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

def get_sector_analysis(db: Session) -> Dict[str, Any]:
    """
    Get sector allocation and diversification analysis for current holdings
    """
    try:
        from backend.utils.portfolio_calculator import get_current_holdings_with_quantities
        from backend.utils.stock_fetcher import get_latest_price
        
        holdings = get_current_holdings_with_quantities(db)
        if not holdings:
            return {"error": "No stocks currently held in portfolio"}
        
        # Get stock info using yfinance for sector data
        sector_data = {}
        total_value = 0
        
        for symbol, quantity in holdings.items():
            try:
                formatted_symbol = f"{symbol}.IS" if not symbol.endswith('.IS') else symbol
                ticker = yf.Ticker(formatted_symbol)
                info = ticker.info
                
                current_price = get_latest_price(symbol) or 0
                position_value = quantity * current_price
                total_value += position_value
                
                # Get sector information
                sector = info.get('sector', 'Unknown')
                industry = info.get('industry', 'Unknown')
                
                if sector not in sector_data:
                    sector_data[sector] = {
                        'value': 0,
                        'stocks': [],
                        'industries': {}
                    }
                
                sector_data[sector]['value'] += position_value
                sector_data[sector]['stocks'].append({
                    'symbol': symbol,
                    'value': position_value,
                    'percentage': 0  # Will calculate after
                })
                
                if industry not in sector_data[sector]['industries']:
                    sector_data[sector]['industries'][industry] = 0
                sector_data[sector]['industries'][industry] += position_value
                
            except Exception as e:
                print(f"Error getting sector data for {symbol}: {e}")
                continue
        
        # Calculate percentages
        for sector in sector_data:
            sector_data[sector]['percentage'] = round((sector_data[sector]['value'] / total_value) * 100, 2) if total_value > 0 else 0
            for stock in sector_data[sector]['stocks']:
                stock['percentage'] = round((stock['value'] / total_value) * 100, 2) if total_value > 0 else 0
        
        # Diversification score (0-100, higher is more diversified)
        num_sectors = len(sector_data)
        if num_sectors <= 1:
            diversification_score = 0
        elif num_sectors <= 3:
            diversification_score = 40
        elif num_sectors <= 5:
            diversification_score = 70
        else:
            diversification_score = 90
        
        return {
            'sector_allocation': sector_data,
            'total_portfolio_value': round(total_value, 2),
            'diversification_score': diversification_score,
            'num_sectors': num_sectors,
            'num_stocks': len(holdings)
        }
        
    except Exception as e:
        return {"error": f"Error calculating sector analysis: {str(e)}"}

def get_tax_reporting_data(db: Session, year: int = None) -> Dict[str, Any]:
    """
    Calculate capital gains/losses for tax reporting purposes
    """
    try:
        from datetime import datetime
        
        if year is None:
            year = datetime.now().year
        
        # Get all sell transactions for the specified year
        sell_transactions = db.query(models.Transaction).filter(
            models.Transaction.type == 'sell',
            models.Transaction.date >= datetime(year, 1, 1).date(),
            models.Transaction.date <= datetime(year, 12, 31).date()
        ).order_by(models.Transaction.date).all()
        
        if not sell_transactions:
            return {"error": f"No sell transactions found for year {year}"}
        
        tax_data = {
            'year': year,
            'transactions': [],
            'summary': {
                'total_proceeds': 0,
                'total_cost_basis': 0,
                'total_capital_gains': 0,
                'short_term_gains': 0,
                'long_term_gains': 0
            }
        }
        
        for sell_tx in sell_transactions:
            # Get buy transactions for the same symbol before the sell date
            buy_transactions = db.query(models.Transaction).filter(
                models.Transaction.type == 'buy',
                models.Transaction.symbol == sell_tx.symbol,
                models.Transaction.date <= sell_tx.date
            ).order_by(models.Transaction.date).all()
            
            if not buy_transactions:
                continue
            
            # Calculate cost basis using FIFO method
            remaining_quantity = sell_tx.quantity
            total_cost_basis = 0
            
            for buy_tx in buy_transactions:
                if remaining_quantity <= 0:
                    break
                
                quantity_to_use = min(remaining_quantity, buy_tx.quantity)
                cost_basis = quantity_to_use * buy_tx.price
                total_cost_basis += cost_basis
                remaining_quantity -= quantity_to_use
            
            proceeds = sell_tx.quantity * sell_tx.price
            capital_gain = proceeds - total_cost_basis
            
            # Determine if short-term or long-term (assuming 1 year threshold)
            days_held = (sell_tx.date - buy_transactions[0].date).days
            is_long_term = days_held >= 365
            
            transaction_data = {
                'sell_date': sell_tx.date.strftime('%Y-%m-%d'),
                'symbol': sell_tx.symbol,
                'quantity': sell_tx.quantity,
                'sell_price': sell_tx.price,
                'proceeds': round(proceeds, 2),
                'cost_basis': round(total_cost_basis, 2),
                'capital_gain': round(capital_gain, 2),
                'days_held': days_held,
                'is_long_term': is_long_term
            }
            
            tax_data['transactions'].append(transaction_data)
            tax_data['summary']['total_proceeds'] += proceeds
            tax_data['summary']['total_cost_basis'] += total_cost_basis
            tax_data['summary']['total_capital_gains'] += capital_gain
            
            if is_long_term:
                tax_data['summary']['long_term_gains'] += capital_gain
            else:
                tax_data['summary']['short_term_gains'] += capital_gain
        
        # Round summary values
        for key in tax_data['summary']:
            if isinstance(tax_data['summary'][key], float):
                tax_data['summary'][key] = round(tax_data['summary'][key], 2)
        
        return tax_data
        
    except Exception as e:
        return {"error": f"Error calculating tax data: {str(e)}"}

def get_enhanced_dashboard_metrics(db: Session) -> Dict[str, Any]:
    """
    Get comprehensive dashboard metrics for better portfolio insights
    """
    try:
        from backend.utils.portfolio_calculator import get_current_holdings_with_quantities
        from backend.utils.stock_fetcher import get_latest_price
        
        holdings = get_current_holdings_with_quantities(db)
        if not holdings:
            return {"error": "No stocks currently held in portfolio"}
        
        # Get recent performance data (30 days)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        symbols = list(holdings.keys())
        hist_data = get_historical_data(symbols, start_date, end_date)
        
        dashboard_metrics = {
            'portfolio_health': {},
            'top_performers': [],
            'worst_performers': [],
            'concentration_risk': {},
            'momentum_indicators': {},
            'volatility_analysis': {}
        }
        
        total_portfolio_value = 0
        stock_performances = []
        
        # Calculate individual stock metrics
        for symbol, quantity in holdings.items():
            current_price = get_latest_price(symbol) or 0
            position_value = quantity * current_price
            total_portfolio_value += position_value
            
            symbol_col = f"{symbol}.IS"
            if symbol_col in hist_data.columns:
                symbol_data = hist_data[symbol_col].dropna()
                if len(symbol_data) >= 2:
                    # 30-day performance
                    start_price = symbol_data.iloc[0]
                    end_price = symbol_data.iloc[-1]
                    performance_30d = ((end_price - start_price) / start_price) * 100
                    
                    # Volatility (30-day)
                    returns = symbol_data.pct_change().dropna()
                    volatility = returns.std() * np.sqrt(252) * 100  # Annualized
                    
                    stock_performances.append({
                        'symbol': symbol,
                        'position_value': position_value,
                        'performance_30d': round(performance_30d, 2),
                        'volatility': round(volatility, 2),
                        'current_price': current_price
                    })
        
        # Sort by performance
        stock_performances.sort(key=lambda x: x['performance_30d'], reverse=True)
        
        # Top and worst performers
        dashboard_metrics['top_performers'] = stock_performances[:3]
        dashboard_metrics['worst_performers'] = stock_performances[-3:]
        
        # Concentration risk
        if total_portfolio_value > 0:
            concentration_data = []
            for stock in stock_performances:
                weight = (stock['position_value'] / total_portfolio_value) * 100
                concentration_data.append({
                    'symbol': stock['symbol'],
                    'weight': round(weight, 2)
                })
            
            # Check if portfolio is over-concentrated
            max_weight = max(concentration_data, key=lambda x: x['weight'])['weight'] if concentration_data else 0
            is_concentrated = max_weight > 25  # More than 25% in single stock
            
            dashboard_metrics['concentration_risk'] = {
                'is_concentrated': is_concentrated,
                'max_position_weight': round(max_weight, 2),
                'positions': concentration_data
            }
        
        # Portfolio health score (0-100)
        health_score = 100
        if dashboard_metrics['concentration_risk'].get('is_concentrated'):
            health_score -= 20
        
        num_stocks = len(holdings)
        if num_stocks < 5:
            health_score -= 15  # Diversification penalty
        
        avg_volatility = np.mean([stock['volatility'] for stock in stock_performances]) if stock_performances else 0
        if avg_volatility > 30:
            health_score -= 15  # High volatility penalty
        
        dashboard_metrics['portfolio_health'] = {
            'score': max(0, health_score),
            'num_holdings': num_stocks,
            'avg_volatility': round(avg_volatility, 2),
            'total_value': round(total_portfolio_value, 2)
        }
        
        return dashboard_metrics
        
    except Exception as e:
        return {"error": f"Error calculating dashboard metrics: {str(e)}"} 