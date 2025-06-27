import yfinance as yf
import pandas as pd
from datetime import date, timedelta, datetime
from typing import List, Dict, Optional, Any
import numpy as np
from sqlalchemy.orm import Session
from .. import models
from .portfolio_calculator import get_current_holdings, get_user_performance_since_purchase, get_current_holdings_with_quantities
from .stock_fetcher import get_latest_price
import time
import random
import logging
import concurrent.futures

# Configure structured logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Note: Letting yfinance handle sessions internally as recommended

# Known stock splits - this should ideally come from a database
KNOWN_STOCK_SPLITS = {
    'CCOLA': {
        'date': '2024-08-01',
        'ratio': 11.0  # 1 share becomes 11 shares
    }
}

# Cache for successful sector lookups (in-memory cache)
_sector_cache = {}

def log_api_call(func_name, symbol, status, detail=""):
    logging.info(f"API_CALL - Function: {func_name}, Symbol: {symbol}, Status: {status}, Detail: {detail}")

def get_historical_data(symbols: List[str], start_date: date, end_date: date, max_retries=3, delay=1) -> pd.DataFrame:
    """
    Fetches historical closing prices, retrying on failure with a session.
    """
    if not symbols:
        return pd.DataFrame()
        
    # Format symbols once
    formatted_symbols = []
    for s in symbols:
        if s.upper() != 'EURTRY=X' and not s.upper().endswith('.IS'):
            formatted_symbols.append(f"{s}.IS")
        else:
            formatted_symbols.append(s)
    ticker_string = " ".join(formatted_symbols)

    last_error = None
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            # Let yfinance handle the session internally
            data = yf.download(ticker_string, start=start_date, end=end_date, progress=False, auto_adjust=True)
            duration = time.time() - start_time
            if not data.empty:
                log_api_call('yf.download', ticker_string, 'SUCCESS', f'Attempt {attempt + 1}, Duration: {duration:.2f}s')
                # We only need the closing prices
                close_prices = data['Close']
                if isinstance(close_prices, pd.Series):
                    close_prices = close_prices.to_frame(name=formatted_symbols[0])
                # Forward-fill missing values for weekends/holidays
                return close_prices.ffill()
        except Exception as e:
            last_error = e
            duration = time.time() - start_time
            log_api_call('yf.download', ticker_string, 'FAIL', f'Attempt {attempt + 1}, Duration: {duration:.2f}s, Error: {e}')
            if "401" in str(e) or "Unauthorized" in str(e):
                print(f"Attempt {attempt + 1}/{max_retries} to fetch historical data failed: Yahoo API authentication issue")
            else:
                print(f"Attempt {attempt + 1}/{max_retries} to fetch historical data failed: {e}")
        
        if attempt < max_retries - 1:
            # Use a longer delay for 401 errors to avoid rate limiting
            delay_time = (delay + random.uniform(1, 3)) if last_error and "401" in str(last_error) else (delay + random.uniform(0, 1))
            time.sleep(delay_time) 

    print(f"All {max_retries} attempts to fetch historical data failed.")
    return pd.DataFrame() # Return empty dataframe if all retries fail

def adjust_for_stock_splits(hist_data, symbol: str):
    """
    Adjust historical data for known stock splits
    """
    if symbol not in KNOWN_STOCK_SPLITS:
        return hist_data
    
    split_info = KNOWN_STOCK_SPLITS[symbol]
    split_date = pd.to_datetime(split_info['date']).date()
    split_ratio = split_info['ratio']
    
    # Convert the DataFrame index to date for comparison
    hist_data_copy = hist_data.copy()
    hist_data_copy.index = pd.to_datetime(hist_data_copy.index).date
    
    # Adjust prices before the split date
    adjustment_factor = split_ratio
    for idx in hist_data_copy.index:
        if idx < split_date:
            # Adjust OHLC prices (divide by split ratio to make them comparable)
            hist_data.loc[hist_data.index[list(hist_data_copy.index).index(idx)], ['Open', 'High', 'Low', 'Close']] /= adjustment_factor
            # Adjust volume (multiply by split ratio)
            hist_data.loc[hist_data.index[list(hist_data_copy.index).index(idx)], 'Volume'] *= adjustment_factor
    
    return hist_data

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
        
        # Adjust for known stock splits
        hist = adjust_for_stock_splits(hist, symbol)
        
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
        
        # Add split adjustment info if applicable
        split_info = {}
        if symbol in KNOWN_STOCK_SPLITS:
            split_info = {
                'has_split': True,
                'split_date': KNOWN_STOCK_SPLITS[symbol]['date'],
                'split_ratio': KNOWN_STOCK_SPLITS[symbol]['ratio'],
                'note': 'Historical prices have been adjusted for stock split'
            }
        else:
            split_info = {'has_split': False}
        
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
            },
            'split_info': split_info
        }
        
    except Exception as e:
        return {"error": f"Error fetching chart data for {symbol}: {str(e)}"}

def get_portfolio_timeline_data(db: Session, start_date: date, end_date: date) -> Dict[str, Any]:
    """
    Generates a timeline of portfolio value and individual stock performance
    Uses actual user purchase prices for meaningful performance calculations
    """
    try:
        from collections import defaultdict
        
        # Get only currently held stocks
        symbols = get_current_holdings(db)
        if not symbols:
            return {"error": "No stocks currently held in portfolio"}
        
        # Get user performance data for each symbol (based on actual purchases)
        user_performances = {}
        for symbol in symbols:
            perf_data = get_user_performance_since_purchase(db, symbol)
            if "error" not in perf_data:
                user_performances[symbol] = perf_data
        
        # Get historical price data for all symbols
        hist_data = get_historical_data(symbols, start_date, end_date)
        if hist_data.empty:
            return {"error": "No historical data available for timeline"}
        
        # Apply split adjustments to historical data
        for symbol in symbols:
            if symbol in KNOWN_STOCK_SPLITS:
                symbol_col = f"{symbol}.IS"
                if symbol_col in hist_data.columns:
                    split_info = KNOWN_STOCK_SPLITS[symbol]
                    split_date = pd.to_datetime(split_info['date']).date()
                    split_ratio = split_info['ratio']
                    
                    # Adjust historical prices before split date
                    for date_idx in hist_data.index:
                        if date_idx.date() < split_date:
                            hist_data.loc[date_idx, symbol_col] /= split_ratio
        
        # Get all transactions for these symbols (including before start_date for holdings calculation)
        all_transactions = db.query(models.Transaction).filter(
            models.Transaction.symbol.in_(symbols),
            models.Transaction.date <= end_date
        ).order_by(models.Transaction.date).all()
        
        # Calculate holdings evolution over time
        def get_holdings_on_date(target_date):
            holdings = defaultdict(float)
            for tx in all_transactions:
                if tx.date <= target_date:
                    if tx.type == "buy":
                        holdings[tx.symbol] += tx.quantity
                    elif tx.type == "sell":
                        holdings[tx.symbol] -= tx.quantity
                    elif tx.type == "split":
                        holdings[tx.symbol] += tx.quantity
            return {symbol: qty for symbol, qty in holdings.items() if qty > 0}
        
        # Generate timeline data
        timeline_dates = []
        portfolio_values = []
        symbol_data = {}
        
        # Initialize symbol data with user-based performance tracking
        for symbol in symbols:
            if symbol in user_performances:
                symbol_data[symbol] = {
                    'daily_returns': [],
                    'cumulative_performance': [],
                    'user_cost_basis': user_performances[symbol]['average_purchase_price'],
                    'first_purchase_date': user_performances[symbol]['first_purchase_date']
                }
        
        # Get valid trading dates from historical data
        valid_dates = hist_data.index.tolist()
        prev_prices = {}
        
        for date in valid_dates:
            current_date = date.date()
            timeline_dates.append(date.strftime('%Y-%m-%d'))
            
            # Get holdings on this date
            current_holdings = get_holdings_on_date(current_date)
            
            # Calculate portfolio value and individual performances
            total_portfolio_value = 0
            
            for symbol in symbols:
                symbol_col = f"{symbol}.IS"
                if symbol_col in hist_data.columns and not pd.isna(hist_data.loc[date, symbol_col]):
                    current_price = float(hist_data.loc[date, symbol_col])
                    quantity = current_holdings.get(symbol, 0)
                    
                    # Calculate position value
                    position_value = quantity * current_price
                    total_portfolio_value += position_value
                    
                    if symbol in symbol_data:
                        # Calculate daily return
                        if symbol in prev_prices and prev_prices[symbol] > 0:
                            daily_return = (current_price - prev_prices[symbol]) / prev_prices[symbol]
                        else:
                            daily_return = 0.0
                        
                        symbol_data[symbol]['daily_returns'].append(round(daily_return, 6))
                        
                        # Calculate cumulative performance from user's average purchase price
                        user_avg_price = symbol_data[symbol]['user_cost_basis']
                        if user_avg_price > 0:
                            cumulative_performance = (current_price - user_avg_price) / user_avg_price
                        else:
                            cumulative_performance = 0.0
                        
                        symbol_data[symbol]['cumulative_performance'].append(round(cumulative_performance, 6))
                        
                        # Update previous price
                        prev_prices[symbol] = current_price
                else:
                    # No data for this date, use previous values
                    for symbol in symbol_data:
                        if symbol_data[symbol]['daily_returns']:
                            symbol_data[symbol]['daily_returns'].append(0.0)
                            symbol_data[symbol]['cumulative_performance'].append(
                                symbol_data[symbol]['cumulative_performance'][-1]
                            )
                        else:
                            symbol_data[symbol]['daily_returns'].append(0.0)
                            symbol_data[symbol]['cumulative_performance'].append(0.0)
            
            portfolio_values.append(round(total_portfolio_value, 2))
        
        # Clean up symbol data - only include symbols with actual data
        clean_symbol_data = {}
        for symbol, data in symbol_data.items():
            if any(val != 0 for val in data['cumulative_performance']):
                # Remove internal fields before returning
                clean_data = {
                    'daily_returns': data['daily_returns'],
                    'cumulative_performance': data['cumulative_performance']
                }
                clean_symbol_data[symbol] = clean_data
        
        return {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "dates": timeline_dates,
            "portfolio_performance": portfolio_values,
            "symbols": clean_symbol_data,
            "user_performance_summary": user_performances  # Add actual user performance data
        }
        
    except Exception as e:
        print(f"Portfolio timeline error: {str(e)}")
        import traceback
        traceback.print_exc()
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

def calculate_risk_score(volatility: float, sharpe_ratio: float, max_drawdown: float, annual_return: float) -> int:
    """
    Calculate a comprehensive risk score (0-100, lower is riskier)
    """
    score = 50  # Start with neutral score
    
    # Volatility component (30% weight)
    if volatility < 20:
        score += 15  # Low volatility is good
    elif volatility < 35:
        score += 5   # Moderate volatility
    elif volatility < 50:
        score -= 5   # High volatility
    else:
        score -= 15  # Very high volatility
    
    # Sharpe ratio component (25% weight)
    if sharpe_ratio > 1.0:
        score += 12
    elif sharpe_ratio > 0.5:
        score += 8
    elif sharpe_ratio > 0:
        score += 3
    else:
        score -= 10
    
    # Max drawdown component (25% weight)
    if max_drawdown > -10:
        score += 12  # Small drawdowns
    elif max_drawdown > -20:
        score += 6   # Moderate drawdowns
    elif max_drawdown > -35:
        score -= 3   # Large drawdowns
    else:
        score -= 12  # Very large drawdowns
    
    # Annual return component (20% weight)
    if annual_return > 15:
        score += 10
    elif annual_return > 5:
        score += 5
    elif annual_return > -5:
        score += 0
    else:
        score -= 8
    
    return max(0, min(100, score))

def generate_investment_signal(performance: float, volatility: float, sharpe_ratio: float, 
                             max_drawdown: float, annual_return: float, days_held: int) -> Dict[str, str]:
    """
    Generate actionable investment recommendations based on metrics
    """
    signal_strength = "NEUTRAL"
    action = "HOLD"
    reasoning = []
    
    # Performance-based signals
    if performance > 25:
        reasoning.append("Strong positive performance (+25%)")
        if volatility < 30:
            signal_strength = "STRONG_HOLD"
            action = "STRONG_BUY"
        else:
            signal_strength = "HOLD"
            action = "TAKE_PROFIT"
    elif performance > 10:
        reasoning.append("Good performance (+10%)")
        action = "HOLD"
    elif performance < -20:
        reasoning.append("Poor performance (-20%)")
        if days_held > 365:
            action = "CONSIDER_SELL"
            signal_strength = "WEAK"
        else:
            action = "MONITOR_CLOSELY"
    elif performance < -10:
        reasoning.append("Negative performance (-10%)")
        action = "MONITOR_CLOSELY"
    
    # Risk-based adjustments
    if volatility > 50:
        reasoning.append("High volatility (>50%)")
        if action == "STRONG_BUY":
            action = "BUY_SMALL"
        elif action == "HOLD":
            action = "REDUCE_POSITION"
    elif volatility < 25:
        reasoning.append("Low volatility (<25%)")
        if action == "HOLD" and performance > 5:
            action = "BUY_MORE"
    
    # Sharpe ratio considerations
    if sharpe_ratio < -0.5:
        reasoning.append("Poor risk-adjusted returns")
        if action not in ["CONSIDER_SELL", "REDUCE_POSITION"]:
            action = "REDUCE_POSITION"
    elif sharpe_ratio > 1.0:
        reasoning.append("Excellent risk-adjusted returns")
        if action == "HOLD":
            action = "BUY_MORE"
    
    # Drawdown warnings
    if max_drawdown < -40:
        reasoning.append("Large historical drawdowns")
        signal_strength = "WEAK"
        if action in ["STRONG_BUY", "BUY_MORE"]:
            action = "BUY_SMALL"
    
    return {
        'action': action,
        'strength': signal_strength,
        'reasoning': "; ".join(reasoning),
        'confidence': "HIGH" if len(reasoning) >= 3 else "MEDIUM" if len(reasoning) >= 2 else "LOW"
    }

def categorize_performance(annual_return: float, volatility: float, sharpe_ratio: float) -> Dict[str, str]:
    """
    Categorize stock performance into grades
    """
    if annual_return > 20 and volatility < 30 and sharpe_ratio > 0.7:
        grade = "A+"
        description = "Excellent: High returns, low risk"
    elif annual_return > 15 and volatility < 40 and sharpe_ratio > 0.5:
        grade = "A"
        description = "Very Good: Strong returns, manageable risk"
    elif annual_return > 10 and volatility < 50:
        grade = "B+"
        description = "Good: Positive returns, moderate risk"
    elif annual_return > 5:
        grade = "B"
        description = "Fair: Modest returns"
    elif annual_return > 0:
        grade = "C"
        description = "Below Average: Minimal returns"
    elif annual_return > -10:
        grade = "D"
        description = "Poor: Negative returns"
    else:
        grade = "F"
        description = "Very Poor: Large losses"
    
    return {
        'grade': grade,
        'description': description
    }

def calculate_position_recommendation(risk_score: int, performance: float, volatility: float) -> Dict[str, Any]:
    """
    Recommend position sizing based on risk and performance
    """
    if risk_score >= 70 and performance > 15:
        size = "LARGE"
        percentage = "15-20%"
        rationale = "High-quality stock with strong performance"
    elif risk_score >= 60 and performance > 10:
        size = "MEDIUM_LARGE"
        percentage = "10-15%"
        rationale = "Good stock with solid performance"
    elif risk_score >= 50 and performance > 0:
        size = "MEDIUM"
        percentage = "5-10%"
        rationale = "Average stock, moderate allocation"
    elif risk_score >= 40:
        size = "SMALL"
        percentage = "2-5%"
        rationale = "Higher risk, smaller position"
    else:
        size = "MINIMAL"
        percentage = "1-3%"
        rationale = "High risk, very small position or consider selling"
    
    return {
        'size': size,
        'percentage_of_portfolio': percentage,
        'rationale': rationale
    }

def calculate_portfolio_insights(risk_metrics: Dict[str, Dict]) -> Dict[str, Any]:
    """
    Calculate portfolio-level insights and recommendations
    """
    if not risk_metrics:
        return {}
    
    # Aggregate portfolio metrics
    total_value = sum(stock['current_value'] for stock in risk_metrics.values())
    weighted_return = sum(stock['annualized_return'] * stock['current_value'] for stock in risk_metrics.values()) / total_value if total_value > 0 else 0
    weighted_volatility = sum(stock['volatility'] * stock['current_value'] for stock in risk_metrics.values()) / total_value if total_value > 0 else 0
    avg_sharpe = sum(stock['sharpe_ratio'] for stock in risk_metrics.values()) / len(risk_metrics)
    
    # Categorize stocks by action
    strong_buys = [symbol for symbol, data in risk_metrics.items() if data['investment_signal']['action'] == 'STRONG_BUY']
    buy_more = [symbol for symbol, data in risk_metrics.items() if data['investment_signal']['action'] == 'BUY_MORE']
    holds = [symbol for symbol, data in risk_metrics.items() if data['investment_signal']['action'] == 'HOLD']
    consider_sells = [symbol for symbol, data in risk_metrics.items() if data['investment_signal']['action'] in ['CONSIDER_SELL', 'REDUCE_POSITION']]
    
    # Calculate portfolio grade
    portfolio_grade = calculate_portfolio_grade(weighted_return, weighted_volatility, avg_sharpe)
    
    # Generate overall strategy recommendation
    strategy_recommendation = generate_portfolio_strategy(strong_buys, buy_more, holds, consider_sells, weighted_return, weighted_volatility)
    
    # Risk concentration analysis
    high_risk_stocks = [symbol for symbol, data in risk_metrics.items() if data['risk_score'] < 40]
    high_risk_exposure = sum(risk_metrics[symbol]['current_value'] for symbol in high_risk_stocks) / total_value * 100 if total_value > 0 else 0
    
    return {
        'portfolio_summary': {
            'total_value': round(total_value, 2),
            'weighted_annual_return': round(weighted_return, 2),
            'weighted_volatility': round(weighted_volatility, 2),
            'average_sharpe_ratio': round(avg_sharpe, 2),
            'portfolio_grade': portfolio_grade
        },
        'action_summary': {
            'strong_buys': strong_buys,
            'buy_more': buy_more,
            'holds': holds,
            'consider_sells': consider_sells,
            'strong_buy_count': len(strong_buys),
            'total_stocks': len(risk_metrics)
        },
        'risk_analysis': {
            'high_risk_stocks': high_risk_stocks,
            'high_risk_exposure_percent': round(high_risk_exposure, 2),
            'risk_level': 'HIGH' if high_risk_exposure > 40 else 'MEDIUM' if high_risk_exposure > 20 else 'LOW'
        },
        'strategy_recommendation': strategy_recommendation
    }

def calculate_portfolio_grade(weighted_return: float, weighted_volatility: float, avg_sharpe: float) -> Dict[str, str]:
    """
    Calculate overall portfolio grade
    """
    if weighted_return > 15 and weighted_volatility < 30 and avg_sharpe > 0.5:
        grade = "A"
        description = "Excellent portfolio performance"
    elif weighted_return > 10 and weighted_volatility < 40:
        grade = "B+"
        description = "Good portfolio performance"
    elif weighted_return > 5:
        grade = "B"
        description = "Fair portfolio performance"
    elif weighted_return > 0:
        grade = "C"
        description = "Below average performance"
    else:
        grade = "D"
        description = "Poor portfolio performance"
    
    return {
        'grade': grade,
        'description': description
    }

def generate_portfolio_strategy(strong_buys: list, buy_more: list, holds: list, 
                              consider_sells: list, weighted_return: float, 
                              weighted_volatility: float) -> Dict[str, str]:
    """
    Generate overall portfolio strategy recommendation
    """
    total_stocks = len(strong_buys) + len(buy_more) + len(holds) + len(consider_sells)
    
    if len(strong_buys) > 0 and weighted_return > 10:
        strategy = "AGGRESSIVE_GROWTH"
        description = f"Focus on {len(strong_buys)} strong performers. Consider increasing positions."
    elif len(buy_more) > total_stocks * 0.4:
        strategy = "MODERATE_GROWTH"
        description = f"Good opportunity to increase positions in {len(buy_more)} stocks."
    elif len(consider_sells) > total_stocks * 0.3:
        strategy = "PORTFOLIO_CLEANUP"
        description = f"Consider reducing or selling {len(consider_sells)} underperforming stocks."
    elif weighted_volatility > 50:
        strategy = "RISK_REDUCTION"
        description = "High portfolio volatility. Focus on stability and risk management."
    else:
        strategy = "BALANCED_HOLD"
        description = "Maintain current positions and monitor performance."
    
    return {
        'strategy': strategy,
        'description': description
    }

def get_risk_metrics(db: Session, period: str = "1y") -> Dict[str, Any]:
    """
    Calculate various risk metrics for portfolio stocks based on user's actual performance
    Properly accounts for dividends, splits, and user's purchase prices
    """
    try:
        # Get only currently held stocks
        symbols = get_current_holdings(db)
        if not symbols:
            return {"error": "No stocks currently held in portfolio"}
        
        # --- OPTIMIZATION: Fetch all latest prices in one batch ---
        end_date_prices = datetime.now()
        start_date_prices = end_date_prices - timedelta(days=2)
        latest_prices_df = get_historical_data(symbols, start_date_prices, end_date_prices)
        
        latest_prices = {}
        if not latest_prices_df.empty:
            for symbol_price in symbols:
                symbol_col_price = f"{symbol_price}.IS"
                if symbol_col_price in latest_prices_df.columns and not latest_prices_df[symbol_col_price].dropna().empty:
                    latest_prices[symbol_price] = latest_prices_df[symbol_col_price].dropna().iloc[-1]
                else:
                    latest_prices[symbol_price] = 0
        # --- END OPTIMIZATION ---

        # Calculate date range for historical data
        end_date = datetime.now().date()
        if period == "1y":
            start_date = end_date - timedelta(days=365)
        elif period == "6mo":
            start_date = end_date - timedelta(days=180)
        else:
            start_date = end_date - timedelta(days=365)  # Default to 1 year
        
        risk_metrics = {}
        
        for symbol in symbols:
            try:
                # Get user's actual performance data (accounts for splits, dividends, purchase price)
                # Pass the pre-fetched price to avoid another API call
                current_price = latest_prices.get(symbol, 0)
                user_perf = get_user_performance_since_purchase(db, symbol, current_price=current_price)
                if "error" in user_perf:
                    continue
                
                # Get transactions for this symbol to calculate daily returns
                transactions = db.query(models.Transaction).filter(
                    models.Transaction.symbol == symbol,
                    models.Transaction.date >= start_date,
                    models.Transaction.date <= end_date
                ).order_by(models.Transaction.date).all()
                
                # Get historical price data (split-adjusted)
                hist_data = get_historical_data([symbol], start_date, end_date)
                if hist_data.empty:
                    continue
                
                symbol_col = f"{symbol}.IS"
                if symbol_col not in hist_data.columns:
                    continue
                
                # Apply split adjustments to historical data
                if symbol in KNOWN_STOCK_SPLITS:
                    split_info = KNOWN_STOCK_SPLITS[symbol]
                    split_date = pd.to_datetime(split_info['date']).date()
                    split_ratio = split_info['ratio']
                    
                    # Adjust historical prices before split date
                    for date_idx in hist_data.index:
                        if date_idx.date() < split_date:
                            hist_data.loc[date_idx, symbol_col] /= split_ratio
                
                # Calculate user-based daily returns (using their cost basis)
                price_data = hist_data[symbol_col].dropna()
                user_cost_basis = user_perf['average_purchase_price']
                
                if len(price_data) < 5 or user_cost_basis <= 0:
                    print(f"Skipping {symbol}: price_data={len(price_data)}, cost_basis={user_cost_basis}")
                    continue
                
                # Calculate returns relative to user's cost basis
                user_returns = []
                prev_price = user_cost_basis  # Start from user's purchase price
                
                for price in price_data:
                    if prev_price > 0:
                        daily_return = (price - prev_price) / prev_price
                        user_returns.append(daily_return)
                    prev_price = price
                
                if len(user_returns) < 5:
                    print(f"Skipping {symbol}: user_returns={len(user_returns)}")
                    continue
                
                user_returns = np.array(user_returns)
                
                # Calculate risk metrics based on user's actual performance
                # 1. Volatility (annualized)
                volatility = float(np.std(user_returns) * np.sqrt(252) * 100)
                
                # 2. User's actual annualized return
                days_held = max(user_perf['days_held'], 1)
                actual_annualized_return = user_perf['annualized_return']
                
                # 3. Sharpe ratio (using user's actual return)
                sharpe_ratio = float(actual_annualized_return / volatility) if volatility > 0 else 0
                
                # 4. Maximum drawdown (from user's cost basis)
                cumulative_values = []
                cumulative_value = 1.0  # Start at 100% of investment
                
                for ret in user_returns:
                    cumulative_value *= (1 + ret)
                    cumulative_values.append(cumulative_value)
                
                cumulative_values = np.array(cumulative_values)
                peak = np.maximum.accumulate(cumulative_values)
                drawdown = (cumulative_values / peak - 1) * 100
                max_drawdown = float(np.min(drawdown))
                
                # 5. Value at Risk (95% confidence)
                var_95 = float(np.percentile(user_returns * 100, 5))
                
                # 6. Additional user-specific metrics
                current_vs_cost_performance = user_perf['return_percentage']
                
                # 7. Calculate risk-adjusted scores and investment recommendations
                risk_score = calculate_risk_score(volatility, sharpe_ratio, max_drawdown, actual_annualized_return)
                investment_signal = generate_investment_signal(
                    current_vs_cost_performance, volatility, sharpe_ratio, 
                    max_drawdown, actual_annualized_return, days_held
                )
                
                # 8. Performance categorization
                performance_grade = categorize_performance(actual_annualized_return, volatility, sharpe_ratio)
                
                # 9. Position sizing recommendation
                position_recommendation = calculate_position_recommendation(
                    risk_score, current_vs_cost_performance, volatility
                )
                
                risk_metrics[symbol] = {
                    'volatility': round(volatility, 2),
                    'annualized_return': round(actual_annualized_return, 2),
                    'sharpe_ratio': round(sharpe_ratio, 2),
                    'max_drawdown': round(max_drawdown, 2),
                    'var_95': round(var_95, 2),
                    'current_performance': round(current_vs_cost_performance, 2),
                    'days_held': user_perf['days_held'],
                    'cost_basis': round(user_perf['cost_basis'], 2),
                    'current_value': round(user_perf['current_value'], 2),
                    'user_avg_price': round(user_perf['average_purchase_price'], 2),
                    'risk_score': risk_score,
                    'investment_signal': investment_signal,
                    'performance_grade': performance_grade,
                    'position_recommendation': position_recommendation
                }
                
            except Exception as e:
                print(f"Error calculating risk metrics for {symbol}: {e}")
                continue
        
        # Calculate portfolio-level insights
        portfolio_insights = calculate_portfolio_insights(risk_metrics)
        
        return {
            'risk_metrics': risk_metrics,
            'portfolio_insights': portfolio_insights,
            'calculation_method': 'user_transaction_based',
            'includes_splits_dividends': True
        }
        
    except Exception as e:
        return {"error": f"Error calculating risk metrics: {str(e)}"}

def get_sector_info_robust(symbol: str, max_retries: int = 2) -> Dict[str, str]:
    """
    Robust sector information fetcher with caching and retry logic.
    Returns: {'sector': str, 'industry': str, 'source': str}
    """
    # Strategy 1: Check in-memory cache first
    if symbol in _sector_cache:
        return {**_sector_cache[symbol], 'source': 'cache'}
    
    # Strategy 2: Try yfinance API with retry logic
    for attempt in range(max_retries):
        try:
            formatted_symbol = f"{symbol}.IS" if not symbol.endswith('.IS') else symbol
            ticker = yf.Ticker(formatted_symbol)
            
            # Add progressive delay to avoid rate limiting
            if attempt > 0:
                delay = random.uniform(0.5, 1.5) * (attempt + 1)
                time.sleep(delay)
            else:
                time.sleep(random.uniform(0.1, 0.3))
            
            start_time = time.time()
            info = ticker.info
            duration = time.time() - start_time
            
            if info and isinstance(info, dict) and 'sector' in info and info['sector'] and info['sector'] != 'Unknown':
                sector_info = {
                    'sector': info.get('sector', 'Unknown'),
                    'industry': info.get('industry', 'Unknown')
                }
                _sector_cache[symbol] = sector_info  # Cache successful result
                log_api_call('get_sector_info', symbol, 'SUCCESS', f'Attempt {attempt + 1}, Duration: {duration:.2f}s')
                return {**sector_info, 'source': 'yfinance_api'}
            else:
                log_api_call('get_sector_info', symbol, 'EMPTY_RESPONSE', f'Attempt {attempt + 1}, Duration: {duration:.2f}s')
                
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            log_api_call('get_sector_info', symbol, 'ERROR', f'Attempt {attempt + 1}, Duration: {duration:.2f}s, Error: {e}')
            if attempt == max_retries - 1:  # Last attempt
                print(f"All {max_retries} attempts failed for {symbol}: {e}")
    
    # Strategy 3: Fallback to Unknown but don't cache this failure
    fallback_info = {'sector': 'Unknown', 'industry': 'Unknown'}
    return {**fallback_info, 'source': 'fallback'}

def get_sector_analysis(db: Session) -> Dict[str, Any]:
    """
    Get sector allocation and diversification analysis for current holdings.
    Uses a robust multi-strategy approach for sector information.
    """
    try:
        holdings = get_current_holdings_with_quantities(db)
        if not holdings:
            return {"error": "No stocks currently held in portfolio"}

        all_symbols = list(holdings.keys())

        # --- OPTIMIZATION: Fetch all latest prices in one batch ---
        end_date = datetime.now()
        start_date = end_date - timedelta(days=2) # 2 days to ensure we get the last closing price
        latest_prices_df = get_historical_data(all_symbols, start_date, end_date)
        
        latest_prices = {}
        if not latest_prices_df.empty:
            for symbol in all_symbols:
                symbol_col = f"{symbol}.IS"
                if symbol_col in latest_prices_df.columns and not latest_prices_df[symbol_col].dropna().empty:
                    latest_prices[symbol] = latest_prices_df[symbol_col].dropna().iloc[-1]
                else:
                    latest_prices[symbol] = 0 # Default to 0 if no price found
        # --- END OPTIMIZATION ---

        sector_data = {}
        total_value = 0
        
        # Use ThreadPoolExecutor for concurrent sector info fetching but with fewer workers
        def fetch_sector_info_with_price(symbol_quantity_tuple):
            symbol, quantity = symbol_quantity_tuple
            try:
                # Get sector info using robust method
                sector_info = get_sector_info_robust(symbol)
                sector = sector_info['sector']
                industry = sector_info['industry']
                source = sector_info['source']
                
                print(f"Sector info for {symbol}: {sector} / {industry} (source: {source})")
                
                # Use the pre-fetched price
                current_price = latest_prices.get(symbol, 0)
                position_value = float(quantity) * float(current_price)
                
                return {
                    'symbol': symbol,
                    'sector': sector,
                    'industry': industry,
                    'position_value': position_value,
                    'source': source
                }
            except Exception as e:
                print(f"Error processing sector data for {symbol}: {e}")
                current_price = latest_prices.get(symbol, 0)
                position_value = float(quantity) * float(current_price)
                return {
                    'symbol': symbol,
                    'sector': 'Unknown',
                    'industry': 'Unknown',
                    'position_value': position_value,
                    'source': 'error'
                }

        # Process stocks with limited concurrency to avoid overwhelming the API
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(fetch_sector_info_with_price, holdings.items()))
        
        # Process results to build sector_data
        for result in results:
            symbol = result['symbol']
            sector = result['sector']
            industry = result['industry']
            position_value = result['position_value']
            
            total_value += position_value
            
            if sector not in sector_data:
                sector_data[sector] = {
                    'value': 0.0,
                    'stocks': [],
                    'industries': {}
                }
            
            sector_data[sector]['value'] += position_value
            sector_data[sector]['stocks'].append({
                'symbol': symbol,
                'value': round(position_value, 2),
                'percentage': 0.0  # Will be calculated later
            })
            
            if industry not in sector_data[sector]['industries']:
                sector_data[sector]['industries'][industry] = 0.0
            sector_data[sector]['industries'][industry] += position_value
        
        # Calculate percentages now that we have the total value
        if total_value > 0:
            for sector_info in sector_data.values():
                sector_info['percentage'] = round((sector_info['value'] / total_value) * 100, 2)
                sector_info['value'] = round(sector_info['value'], 2)
                for stock in sector_info['stocks']:
                    stock['percentage'] = round((stock['value'] / total_value) * 100, 2)
                
                for industry, value in sector_info['industries'].items():
                    sector_info['industries'][industry] = round(float(value), 2)
        
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
            'total_portfolio_value': round(float(total_value), 2),
            'diversification_score': int(diversification_score),
            'num_sectors': int(num_sectors),
            'num_stocks': int(len(holdings))
        }
        
    except Exception as e:
        return {"error": f"Error calculating sector analysis: {str(e)}"}

def get_enhanced_dashboard_metrics(db: Session) -> Dict[str, Any]:
    """
    Get comprehensive dashboard metrics for better portfolio insights
    Uses transaction-based performance accounting for splits and dividends
    """
    try:
        holdings = get_current_holdings_with_quantities(db)
        if not holdings:
            return {"error": "No stocks currently held in portfolio"}
        
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
        
        # --- Start of Optimization ---
        # 1. Get all symbols at once
        all_symbols = list(holdings.keys())
        
        # 2. Fetch 30-day historical data for all symbols in one batch
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        all_hist_data = get_historical_data(all_symbols, start_date, end_date)
        # --- End of Optimization ---

        # Calculate individual stock metrics using user's actual performance data
        for symbol, quantity in holdings.items():
            try:
                current_price = get_latest_price(symbol) or 0
                if current_price == 0:
                    print(f"Could not get current price for {symbol}. Skipping from dashboard metrics.")
                    continue
                position_value = float(quantity) * float(current_price)
                total_portfolio_value += position_value
                
                user_perf = get_user_performance_since_purchase(db, symbol)
                if "error" in user_perf:
                    stock_performances.append({
                        'symbol': symbol,
                        'position_value': round(position_value, 2),
                        'performance_30d': 0.0,
                        'gain_loss_30d_try': 0.0,
                        'current_price': round(float(current_price), 2),
                        'user_return': 0.0,
                        'days_held': 0,
                        'annualized_return': 0.0
                    })
                    continue
                
                # Use the pre-fetched historical data
                performance_30d = 0.0
                gain_loss_30d_try = 0.0
                
                if not all_hist_data.empty:
                    symbol_col = f"{symbol}.IS"
                    if symbol_col in all_hist_data.columns:
                        hist_data_for_symbol = all_hist_data[[symbol_col]].copy()
                        # Apply split adjustments
                        if symbol in KNOWN_STOCK_SPLITS:
                            split_info = KNOWN_STOCK_SPLITS[symbol]
                            split_date = pd.to_datetime(split_info['date']).date()
                            split_ratio = split_info['ratio']
                            
                            for date_idx in hist_data_for_symbol.index:
                                if date_idx.date() < split_date:
                                    hist_data_for_symbol.loc[date_idx, symbol_col] /= split_ratio
                        
                        symbol_data = hist_data_for_symbol[symbol_col].dropna()
                        if len(symbol_data) >= 2:
                            start_price = float(symbol_data.iloc[0])
                            end_price = float(symbol_data.iloc[-1])
                            performance_30d = ((end_price - start_price) / start_price) * 100 if start_price > 0 else 0
                            price_change = end_price - start_price
                            gain_loss_30d_try = price_change * float(quantity)
                
                stock_performances.append({
                    'symbol': symbol,
                    'position_value': round(position_value, 2),
                    'performance_30d': round(performance_30d, 2),
                    'gain_loss_30d_try': round(gain_loss_30d_try, 2),
                    'current_price': round(float(current_price), 2),
                    'user_return': round(user_perf['return_percentage'], 2),
                    'days_held': user_perf['days_held'],
                    'annualized_return': round(user_perf['annualized_return'], 2)
                })
                
            except Exception as e:
                print(f"Error calculating dashboard metrics for {symbol}: {e}")
                continue
        
        # Sort by 30-day performance for top/worst performers
        # Separate stocks into positive and negative performance for accurate top/worst lists
        positive_performers_30d = sorted([p for p in stock_performances if p['performance_30d'] >= 0], key=lambda x: x['performance_30d'], reverse=True)
        negative_performers_30d = sorted([p for p in stock_performances if p['performance_30d'] < 0], key=lambda x: x['performance_30d'])

        # Portfolio health metrics
        num_holdings = len(holdings)
        
        # Simple health score based on diversification and performance
        diversification_score = min(num_holdings * 10, 40)  # Max 40 points for diversification
        
        # Performance score based on positive vs negative performers
        positive_performers = len([p for p in stock_performances if p['user_return'] > 0])
        performance_score = (positive_performers / len(stock_performances)) * 40 if stock_performances else 0
        
        # Risk score based on 30-day gains/losses
        positive_30d_performers = len([p for p in stock_performances if p['performance_30d'] > 0])
        momentum_score = (positive_30d_performers / len(stock_performances)) * 20 if stock_performances else 0
        
        health_score = round(diversification_score + performance_score + momentum_score)
        
        dashboard_metrics['portfolio_health'] = {
            'score': min(health_score, 100),
            'num_holdings': num_holdings,
            'positive_30d_performers': positive_30d_performers,
            'total_value': round(total_portfolio_value, 2),
            'positive_performers': positive_performers,
            'total_performers': len(stock_performances)
        }
        
        # Concentration Risk
        if total_portfolio_value > 0 and stock_performances:
            stock_performances.sort(key=lambda x: x['position_value'], reverse=True)
            top_3_positions = stock_performances[:3]
            top_3_value = sum(p['position_value'] for p in top_3_positions)
            
            dashboard_metrics['concentration_risk'] = {
                'is_concentrated': (top_3_value / total_portfolio_value) > 0.5,
                'top_3_percentage': round((top_3_value / total_portfolio_value) * 100, 2),
                'max_position_weight': round((top_3_positions[0]['position_value'] / total_portfolio_value) * 100, 2) if top_3_positions else 0,
                'positions': [{
                    'symbol': p['symbol'],
                    'weight': round((p['position_value'] / total_portfolio_value) * 100, 2)
                } for p in top_3_positions]
            }
        else:
            # Ensure a default structure is always returned
            dashboard_metrics['concentration_risk'] = {
                'is_concentrated': False,
                'top_3_percentage': 0,
                'max_position_weight': 0,
                'positions': []
            }
        
        dashboard_metrics['top_performers'] = positive_performers_30d[:5]
        dashboard_metrics['worst_performers'] = negative_performers_30d[:5]
        
        return dashboard_metrics
        
    except Exception as e:
        return {"error": f"Error calculating dashboard metrics: {str(e)}"} 