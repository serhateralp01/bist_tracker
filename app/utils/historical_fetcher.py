import yfinance as yf
import pandas as pd
from datetime import date, timedelta, datetime
from typing import List, Dict, Optional, Any
import numpy as np
from sqlalchemy.orm import Session
from app import models
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

# Cache for dashboard metrics to ensure stability within short time windows
_dashboard_cache = {}
_cache_ttl = 30  # 30 seconds cache time

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

def calculate_advanced_risk_score(volatility: float, sharpe_ratio: float, max_drawdown: float, 
                                annual_return: float, sortino_ratio: float = 0, beta: float = 1,
                                momentum_6m: float = 0, rsi: float = 50) -> Dict[str, Any]:
    """
    Calculate a comprehensive risk score with advanced metrics (0-100, higher is better)
    """
    base_score = 50  # Start with neutral score
    
    # Core Risk Metrics (60% weight)
    # Volatility component (20% weight)
    if volatility < 15:
        volatility_score = 20  # Very low volatility - excellent
    elif volatility < 25:
        volatility_score = 15  # Low volatility - good
    elif volatility < 35:
        volatility_score = 10  # Moderate volatility - fair
    elif volatility < 50:
        volatility_score = 0   # High volatility - neutral
    elif volatility < 70:
        volatility_score = -10 # Very high volatility - poor
    else:
        volatility_score = -20 # Extreme volatility - very poor
    
    # Sharpe ratio component (20% weight) 
    if sharpe_ratio > 1.5:
        sharpe_score = 20  # Excellent risk-adjusted returns
    elif sharpe_ratio > 1.0:
        sharpe_score = 15  # Very good
    elif sharpe_ratio > 0.5:
        sharpe_score = 10  # Good
    elif sharpe_ratio > 0:
        sharpe_score = 5   # Fair
    elif sharpe_ratio > -0.5:
        sharpe_score = -5  # Poor
    else:
        sharpe_score = -15 # Very poor
    
    # Max drawdown component (20% weight)
    if max_drawdown > -5:
        drawdown_score = 20  # Minimal drawdowns - excellent
    elif max_drawdown > -10:
        drawdown_score = 15  # Small drawdowns - very good
    elif max_drawdown > -20:
        drawdown_score = 10  # Moderate drawdowns - good
    elif max_drawdown > -35:
        drawdown_score = 0   # Large drawdowns - neutral
    elif max_drawdown > -50:
        drawdown_score = -10 # Very large drawdowns - poor
    else:
        drawdown_score = -20 # Extreme drawdowns - very poor
    
    # Advanced Metrics (25% weight)
    # Sortino ratio (better than Sharpe for downside risk) (8% weight)
    if sortino_ratio > 1.0:
        sortino_score = 8
    elif sortino_ratio > 0.5:
        sortino_score = 5
    elif sortino_ratio > 0:
        sortino_score = 2
    else:
        sortino_score = -5
    
    # Beta (market correlation) (8% weight)
    if 0.8 <= beta <= 1.2:
        beta_score = 8   # Well-correlated with market
    elif 0.6 <= beta <= 1.4:
        beta_score = 5   # Moderately correlated
    elif beta < 0.6:
        beta_score = 3   # Low correlation (defensive)
    else:
        beta_score = -5  # High beta (aggressive)
    
    # 6-month momentum (9% weight)
    if momentum_6m > 15:
        momentum_score = 9   # Strong positive momentum
    elif momentum_6m > 5:
        momentum_score = 6   # Good momentum
    elif momentum_6m > -5:
        momentum_score = 3   # Neutral momentum
    elif momentum_6m > -15:
        momentum_score = -3  # Poor momentum
    else:
        momentum_score = -9  # Very poor momentum
    
    # Performance Quality (15% weight)
    # Annual return component (15% weight)
    if annual_return > 25:
        return_score = 15  # Exceptional returns
    elif annual_return > 15:
        return_score = 12  # Excellent returns
    elif annual_return > 10:
        return_score = 8   # Good returns
    elif annual_return > 5:
        return_score = 5   # Fair returns
    elif annual_return > 0:
        return_score = 2   # Modest returns
    elif annual_return > -10:
        return_score = -5  # Poor returns
    else:
        return_score = -15 # Very poor returns
    
    # Calculate final score
    final_score = (base_score + volatility_score + sharpe_score + drawdown_score + 
                  sortino_score + beta_score + momentum_score + return_score)
    
    # Ensure score is between 0 and 100
    final_score = max(0, min(100, final_score))
    
    # Calculate risk categories
    if final_score >= 80:
        risk_category = "VERY_LOW"
        risk_description = "Excellent risk-reward profile"
    elif final_score >= 65:
        risk_category = "LOW"
        risk_description = "Good risk-reward profile"
    elif final_score >= 50:
        risk_category = "MODERATE"
        risk_description = "Balanced risk-reward profile"
    elif final_score >= 35:
        risk_category = "HIGH"
        risk_description = "Higher risk investment"
    else:
        risk_category = "VERY_HIGH"
        risk_description = "High risk investment"
    
    return {
        'risk_score': int(final_score),
        'risk_category': risk_category,
        'risk_description': risk_description,
        'component_scores': {
            'volatility': volatility_score,
            'sharpe_ratio': sharpe_score,
            'max_drawdown': drawdown_score,
            'sortino_ratio': sortino_score,
            'beta': beta_score,
            'momentum_6m': momentum_score,
            'annual_return': return_score
        }
    }

def generate_enhanced_investment_signal(performance: float, volatility: float, sharpe_ratio: float, 
                                      max_drawdown: float, annual_return: float, days_held: int,
                                      risk_score: int, grade_points: float, momentum_6m: float = 0) -> Dict[str, str]:
    """
    Generate sophisticated investment recommendations based on comprehensive metrics
    """
    reasoning_factors = []
    confidence_score = 0
    
    # Performance analysis
    if performance > 30:
        reasoning_factors.append("Exceptional performance (+30%)")
        confidence_score += 25
        base_action = "STRONG_BUY"
    elif performance > 15:
        reasoning_factors.append("Strong performance (+15%)")
        confidence_score += 20
        base_action = "BUY_MORE"
    elif performance > 5:
        reasoning_factors.append("Positive performance (+5%)")
        confidence_score += 10
        base_action = "HOLD"
    elif performance > -10:
        reasoning_factors.append("Minor losses (-10%)")
        confidence_score += 5
        base_action = "MONITOR"
    elif performance > -25:
        reasoning_factors.append("Significant losses (-25%)")
        confidence_score -= 10
        base_action = "REDUCE_POSITION"
    else:
        reasoning_factors.append("Major losses (-25%+)")
        confidence_score -= 20
        base_action = "CONSIDER_SELL"
    
    # Risk-adjusted performance analysis
    if sharpe_ratio > 1.5:
        reasoning_factors.append("Excellent risk-adjusted returns (Sharpe > 1.5)")
        confidence_score += 20
        if base_action in ["HOLD", "MONITOR"]:
            base_action = "BUY_MORE"
    elif sharpe_ratio > 1.0:
        reasoning_factors.append("Good risk-adjusted returns (Sharpe > 1.0)")
        confidence_score += 15
    elif sharpe_ratio > 0.5:
        reasoning_factors.append("Fair risk-adjusted returns")
        confidence_score += 5
    elif sharpe_ratio < 0:
        reasoning_factors.append("Poor risk-adjusted returns")
        confidence_score -= 15
        if base_action == "BUY_MORE":
            base_action = "HOLD"
        elif base_action == "HOLD":
            base_action = "MONITOR"
    
    # Volatility considerations
    if volatility > 60:
        reasoning_factors.append("Very high volatility (>60%)")
        confidence_score -= 15
        if base_action in ["STRONG_BUY", "BUY_MORE"]:
            base_action = "BUY_SMALL"
    elif volatility > 40:
        reasoning_factors.append("High volatility (>40%)")
        confidence_score -= 10
        if base_action == "STRONG_BUY":
            base_action = "BUY_MORE"
    elif volatility < 25:
        reasoning_factors.append("Low volatility (<25%)")
        confidence_score += 10
        if base_action == "HOLD" and performance > 0:
            base_action = "BUY_MORE"
    
    # Drawdown analysis
    if max_drawdown < -40:
        reasoning_factors.append("Severe historical drawdowns (-40%+)")
        confidence_score -= 20
        if base_action in ["STRONG_BUY", "BUY_MORE"]:
            base_action = "BUY_SMALL"
    elif max_drawdown < -25:
        reasoning_factors.append("Large historical drawdowns (-25%)")
        confidence_score -= 10
    elif max_drawdown > -10:
        reasoning_factors.append("Minimal historical drawdowns")
        confidence_score += 15
    
    # Time-based factors
    if days_held < 90:
        reasoning_factors.append("Recently acquired (< 3 months)")
        confidence_score += 5
    elif days_held > 730:
        reasoning_factors.append("Long-term holding (2+ years)")
        if performance < -15:
            reasoning_factors.append("Long-term underperformance suggests reconsideration")
            confidence_score -= 10
        else:
            confidence_score += 5
    
    # Risk score integration
    if risk_score >= 80:
        reasoning_factors.append("Very low risk profile")
        confidence_score += 15
        if base_action == "MONITOR":
            base_action = "HOLD"
    elif risk_score >= 65:
        reasoning_factors.append("Low risk profile")
        confidence_score += 10
    elif risk_score < 40:
        reasoning_factors.append("High risk profile")
        confidence_score -= 15
        if base_action in ["STRONG_BUY", "BUY_MORE"]:
            base_action = "BUY_SMALL"
    
    # Grade-based adjustments
    if grade_points >= 4.0:
        reasoning_factors.append("A-grade investment quality")
        confidence_score += 20
        if base_action == "HOLD":
            base_action = "BUY_MORE"
    elif grade_points >= 3.0:
        reasoning_factors.append("B-grade investment quality")
        confidence_score += 10
    elif grade_points < 2.0:
        reasoning_factors.append("Poor investment grade (C- or below)")
        confidence_score -= 20
        if base_action not in ["REDUCE_POSITION", "CONSIDER_SELL"]:
            base_action = "REDUCE_POSITION"
    
    # Momentum considerations (if available)
    if momentum_6m > 15:
        reasoning_factors.append("Strong positive momentum")
        confidence_score += 10
    elif momentum_6m < -15:
        reasoning_factors.append("Negative momentum trend")
        confidence_score -= 10
    
    # Final action determination based on comprehensive analysis
    final_actions = {
        "STRONG_BUY": "STRONG_BUY",
        "BUY_MORE": "BUY_MORE", 
        "BUY_SMALL": "BUY_SMALL",
        "HOLD": "HOLD",
        "MONITOR": "MONITOR_CLOSELY",
        "REDUCE_POSITION": "REDUCE_POSITION",
        "CONSIDER_SELL": "CONSIDER_SELL"
    }
    
    final_action = final_actions.get(base_action, "HOLD")
    
    # Determine confidence level
    if confidence_score >= 60:
        confidence = "VERY_HIGH"
    elif confidence_score >= 40:
        confidence = "HIGH"
    elif confidence_score >= 20:
        confidence = "MEDIUM"
    elif confidence_score >= 0:
        confidence = "LOW"
    else:
        confidence = "VERY_LOW"
    
    # Determine signal strength
    if confidence_score >= 50 and final_action in ["STRONG_BUY", "BUY_MORE"]:
        strength = "STRONG_POSITIVE"
    elif confidence_score >= 30 and final_action in ["BUY_MORE", "BUY_SMALL"]:
        strength = "POSITIVE"
    elif final_action == "HOLD":
        strength = "NEUTRAL"
    elif final_action in ["REDUCE_POSITION", "CONSIDER_SELL"]:
        strength = "NEGATIVE"
    else:
        strength = "NEUTRAL"
    
    return {
        'action': final_action,
        'strength': strength,
        'reasoning': "; ".join(reasoning_factors),
        'confidence': confidence,
        'confidence_score': confidence_score
    }

def categorize_advanced_performance(annual_return: float, volatility: float, sharpe_ratio: float,
                                   sortino_ratio: float = 0, max_drawdown: float = 0, 
                                   risk_score: int = 50) -> Dict[str, Any]:
    """
    Enhanced stock performance categorization with sophisticated grading
    """
    # Base score calculation
    score = 0
    
    # Return component (35% weight)
    if annual_return > 30:
        return_points = 35
    elif annual_return > 20:
        return_points = 30
    elif annual_return > 15:
        return_points = 25
    elif annual_return > 10:
        return_points = 20
    elif annual_return > 5:
        return_points = 15
    elif annual_return > 0:
        return_points = 10
    elif annual_return > -10:
        return_points = 5
    else:
        return_points = 0
    
    # Risk-adjusted return component (25% weight)
    if sharpe_ratio > 2.0:
        sharpe_points = 25
    elif sharpe_ratio > 1.5:
        sharpe_points = 22
    elif sharpe_ratio > 1.0:
        sharpe_points = 18
    elif sharpe_ratio > 0.5:
        sharpe_points = 14
    elif sharpe_ratio > 0:
        sharpe_points = 10
    elif sharpe_ratio > -0.5:
        sharpe_points = 5
    else:
        sharpe_points = 0
    
    # Volatility component (20% weight) - inverted (lower is better)
    if volatility < 15:
        vol_points = 20
    elif volatility < 25:
        vol_points = 17
    elif volatility < 35:
        vol_points = 14
    elif volatility < 50:
        vol_points = 10
    elif volatility < 70:
        vol_points = 6
    else:
        vol_points = 0
    
    # Drawdown resilience (10% weight)
    if max_drawdown > -10:
        drawdown_points = 10
    elif max_drawdown > -20:
        drawdown_points = 8
    elif max_drawdown > -35:
        drawdown_points = 5
    elif max_drawdown > -50:
        drawdown_points = 2
    else:
        drawdown_points = 0
    
    # Sortino ratio bonus (10% weight)
    if sortino_ratio > 1.5:
        sortino_points = 10
    elif sortino_ratio > 1.0:
        sortino_points = 8
    elif sortino_ratio > 0.5:
        sortino_points = 5
    elif sortino_ratio > 0:
        sortino_points = 3
    else:
        sortino_points = 0
    
    # Calculate total score
    total_score = return_points + sharpe_points + vol_points + drawdown_points + sortino_points
    
    # Determine grade and detailed analysis
    if total_score >= 90:
        grade = "A+"
        grade_points = 4.3
        description = "Outstanding: Exceptional returns with minimal risk"
        investment_tier = "TIER_1_PREMIUM"
        recommendation = "Core holding - maximize position"
    elif total_score >= 85:
        grade = "A"
        grade_points = 4.0
        description = "Excellent: Strong returns with low risk"
        investment_tier = "TIER_1"
        recommendation = "Core holding - large position"
    elif total_score >= 80:
        grade = "A-"
        grade_points = 3.7
        description = "Very Good: Solid returns with manageable risk"
        investment_tier = "TIER_2"
        recommendation = "Strong buy - significant position"
    elif total_score >= 75:
        grade = "B+"
        grade_points = 3.3
        description = "Good: Positive returns with moderate risk"
        investment_tier = "TIER_2"
        recommendation = "Buy - moderate position"
    elif total_score >= 65:
        grade = "B"
        grade_points = 3.0
        description = "Fair: Decent returns with acceptable risk"
        investment_tier = "TIER_3"
        recommendation = "Hold - maintain position"
    elif total_score >= 55:
        grade = "B-"
        grade_points = 2.7
        description = "Below Average: Mixed performance"
        investment_tier = "TIER_3"
        recommendation = "Monitor closely"
    elif total_score >= 45:
        grade = "C+"
        grade_points = 2.3
        description = "Weak: Underperforming with elevated risk"
        investment_tier = "TIER_4"
        recommendation = "Consider reducing position"
    elif total_score >= 35:
        grade = "C"
        grade_points = 2.0
        description = "Poor: Negative returns with high risk"
        investment_tier = "TIER_4"
        recommendation = "Reduce position significantly"
    elif total_score >= 25:
        grade = "D"
        grade_points = 1.0
        description = "Very Poor: Large losses with very high risk"
        investment_tier = "TIER_5"
        recommendation = "Consider selling"
    else:
        grade = "F"
        grade_points = 0.0
        description = "Failing: Severe losses with extreme risk"
        investment_tier = "TIER_5"
        recommendation = "Sell immediately"
    
    # Add qualitative factors
    risk_quality = "Low" if risk_score >= 70 else "Moderate" if risk_score >= 50 else "High"
    return_quality = "Excellent" if annual_return > 20 else "Good" if annual_return > 10 else "Fair" if annual_return > 0 else "Poor"
    
    return {
        'grade': grade,
        'grade_points': grade_points,
        'description': description,
        'investment_tier': investment_tier,
        'recommendation': recommendation,
        'score_breakdown': {
            'total_score': total_score,
            'return_points': return_points,
            'sharpe_points': sharpe_points,
            'volatility_points': vol_points,
            'drawdown_points': drawdown_points,
            'sortino_points': sortino_points
        },
        'qualitative_assessment': {
            'risk_quality': risk_quality,
            'return_quality': return_quality,
            'overall_assessment': f"{return_quality} returns with {risk_quality.lower()} risk"
        }
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
                
                # 7. Calculate risk-adjusted scores
                risk_score = calculate_advanced_risk_score(volatility, sharpe_ratio, max_drawdown, actual_annualized_return)
                
                # 8. Performance categorization
                performance_grade = categorize_advanced_performance(actual_annualized_return, volatility, sharpe_ratio,
                                                                     risk_score=risk_score['risk_score'],
                                                                     max_drawdown=max_drawdown)
                
                # 9. Investment recommendations
                investment_signal = generate_enhanced_investment_signal(
                    current_vs_cost_performance, volatility, sharpe_ratio, 
                    max_drawdown, actual_annualized_return, days_held,
                    risk_score['risk_score'], performance_grade['grade_points']
                )
                
                # 9. Position sizing recommendation
                position_recommendation = calculate_position_recommendation(
                    risk_score['risk_score'], current_vs_cost_performance, volatility
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
                    'risk_score': risk_score['risk_score'],
                    'risk_category': risk_score['risk_category'],
                    'risk_description': risk_score['risk_description'],
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
        # Check cache first to ensure stability within short time windows
        cache_key = "dashboard_metrics"
        current_time = time.time()
        
        if cache_key in _dashboard_cache:
            cached_data, timestamp = _dashboard_cache[cache_key]
            if current_time - timestamp < _cache_ttl:
                return cached_data
        
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
        # 1. Get all symbols at once and sort for consistent ordering
        all_symbols = sorted(list(holdings.keys()))  # Sort for deterministic order
        
        # 2. Fetch current prices and 30-day historical data in batches for consistency
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Get both current prices and historical data in one batch call
        all_hist_data = get_historical_data(all_symbols, start_date, end_date)
        
        # Extract current prices from the historical data for consistency
        current_prices = {}
        if not all_hist_data.empty:
            for symbol in all_symbols:
                symbol_col = f"{symbol}.IS"
                if symbol_col in all_hist_data.columns:
                    symbol_data = all_hist_data[symbol_col].dropna()
                    if len(symbol_data) > 0:
                        current_prices[symbol] = float(symbol_data.iloc[-1])
                    else:
                        current_prices[symbol] = 0.0
                else:
                    current_prices[symbol] = 0.0
        # --- End of Optimization ---

        # Calculate individual stock metrics using user's actual performance data
        # Process symbols in sorted order for consistent results
        for symbol in sorted(holdings.keys()):
            try:
                quantity = holdings[symbol]  # Get quantity for this symbol
                # Use batch-fetched current price for consistency
                current_price = current_prices.get(symbol, 0.0)
                if current_price == 0:
                    # Fallback to individual API call only if batch failed
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
                            # Use high precision and consistent rounding
                            performance_30d = round(((end_price - start_price) / start_price) * 100, 4) if start_price > 0 else 0.0
                            price_change = end_price - start_price
                            gain_loss_30d_try = round(price_change * float(quantity), 4)
                
                stock_performances.append({
                    'symbol': symbol,
                    'position_value': round(position_value, 2),
                    'performance_30d': round(performance_30d, 4),  # Higher precision for stable sorting
                    'gain_loss_30d_try': round(gain_loss_30d_try, 2),
                    'current_price': round(float(current_price), 2),
                    'user_return': round(user_perf['return_percentage'], 2),
                    'days_held': user_perf['days_held'],
                    'annualized_return': round(user_perf['annualized_return'], 2)
                })
                
            except Exception as e:
                print(f"Error calculating dashboard metrics for {symbol}: {e}")
                continue
        
        # Sort by 30-day performance for top/worst performers with stable sorting
        # Use multiple criteria for deterministic ordering: performance_30d, position_value, symbol
        positive_performers_30d = sorted(
            [p for p in stock_performances if p['performance_30d'] >= 0], 
            key=lambda x: (x['performance_30d'], x['position_value'], x['symbol']), 
            reverse=True
        )
        negative_performers_30d = sorted(
            [p for p in stock_performances if p['performance_30d'] < 0], 
            key=lambda x: (x['performance_30d'], -x['position_value'], x['symbol'])  # Note: negative position_value for secondary sort
        )

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
            # Create a separate copy for concentration analysis to avoid affecting performance sorting
            concentration_sorted = sorted(stock_performances, key=lambda x: (x['position_value'], x['symbol']), reverse=True)
            top_3_positions = concentration_sorted[:3]
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
        
        # Cache the result for stability
        _dashboard_cache[cache_key] = (dashboard_metrics, current_time)
        
        return dashboard_metrics
        
    except Exception as e:
        return {"error": f"Error calculating dashboard metrics: {str(e)}"} 