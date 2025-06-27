from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, HTTPException, File, UploadFile
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from backend import models, schemas, crud
from backend.database import SessionLocal, engine
from backend.utils.message_parser import parse_message
from backend.utils.event_parser import parse_event_message
from backend.utils.portfolio_calculator import calculate_portfolio_value
from fastapi import APIRouter
from collections import defaultdict
from datetime import datetime, timedelta, date
from backend.schemas import Transaction
from backend.utils.stock_fetcher import get_latest_price, get_bist100_data
from backend.utils.currency_fetcher import get_latest_eur_try_rate, get_historical_eur_try_rate
from backend.utils.historical_fetcher import (
    get_historical_data,
    get_stock_historical_chart,
    get_portfolio_timeline_data,
    get_market_comparison_data,
    get_risk_metrics,
    get_sector_analysis,
    get_tax_reporting_data,
    get_enhanced_dashboard_metrics
)
from backend.utils.data_import_export import (
    export_transactions_to_csv, 
    export_transactions_to_excel,
    import_transactions_from_csv,
    import_transactions_from_excel,
    create_sample_csv_template
)
import pandas as pd
import io


app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Veritabanını oluştur
models.Base.metadata.create_all(bind=engine)

# DB bağımlılığı
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_holdings_on_date(db: Session, symbol: str, event_date: date) -> float:
    """Calculates the total quantity of a stock held just before a specific date."""
    transactions = db.query(models.Transaction).filter(
        models.Transaction.symbol == symbol,
        models.Transaction.date < event_date
    ).order_by(models.Transaction.date).all()

    quantity = 0.0
    for tx in transactions:
        if tx.type == 'buy':
            quantity += tx.quantity
        elif tx.type == 'sell':
            quantity -= tx.quantity
        elif tx.type == 'split':
            quantity += tx.quantity
    return quantity

router = APIRouter()

@router.get("/portfolio/daily_value", response_model=list[schemas.PortfolioValue])
def get_daily_portfolio_value(db: Session = Depends(get_db)):
    transactions = db.query(models.Transaction).order_by(models.Transaction.date).all()

    if not transactions:
        return []

    # 1. Determine date range and symbols needed
    start_date = transactions[0].date
    end_date = datetime.now().date()
    all_symbols = list(set(tx.symbol for tx in transactions if tx.symbol))
    
    # We need EURTRY=X for currency conversion
    fetch_symbols = all_symbols + ['EURTRY=X']

    # 2. Fetch all historical data in one batch
    hist_data = get_historical_data(fetch_symbols, start_date, end_date)
    
    if hist_data.empty:
        # Fallback or error if we can't get any historical data
        return []

    # 3. Iterate through time and calculate daily values
    holdings = defaultdict(float)
    cash = 0
    portfolio_value_by_day = []
    tx_index = 0
    
    # Use pandas date range for robust iteration
    for current_day_dt in pd.date_range(start=start_date, end=end_date, freq='D'):
        current_day = current_day_dt.date()

        # Update holdings based on transactions for the current day
        while tx_index < len(transactions) and transactions[tx_index].date == current_day:
            tx = transactions[tx_index]
            if tx.type == "buy":
                holdings[tx.symbol] += tx.quantity
                cash -= tx.quantity * tx.price
            elif tx.type == "sell":
                holdings[tx.symbol] -= tx.quantity
                cash += tx.quantity * tx.price
            elif tx.type == "deposit":
                cash += tx.quantity
            elif tx.type == "withdrawal":
                cash -= tx.quantity
            elif tx.type == "dividend":
                cash += tx.price
            elif tx.type == "split":
                holdings[tx.symbol] += tx.quantity
            tx_index += 1

        # Find the latest available prices for the current day from our batch data
        try:
            day_prices = hist_data.asof(current_day_dt)
        except KeyError:
            continue # Skip if date is out of range of our historical data

        # Calculate total portfolio value in TRY (SADECE HİSSELER)
        stock_value_try = 0
        for symbol, qty in holdings.items():
            if qty > 0:
                symbol_col = f"{symbol}.IS" if not symbol.endswith('.IS') else symbol
                if symbol_col in day_prices and pd.notna(day_prices[symbol_col]):
                    stock_value_try += qty * day_prices[symbol_col]

        # Calculate total portfolio value in EUR (SADECE HİSSELER)
        eur_rate = day_prices['EURTRY=X'] if 'EURTRY=X' in day_prices and pd.notna(day_prices['EURTRY=X']) else None
        stock_value_eur = (stock_value_try / eur_rate) if eur_rate and eur_rate > 0 else 0
        
        portfolio_value_by_day.append({
            "date": str(current_day),
            "value_try": round(stock_value_try, 2),
            "value_eur": round(stock_value_eur, 2)
        })

    return portfolio_value_by_day

app.include_router(router)

@app.get("/")
def root():
    return {"message": "BIST Portfolio Tracker Backend is running."}

@app.get("/bist100")
def get_bist100():
    """
    Get current BIST 100 index data
    """
    data = get_bist100_data()
    if data:
        return data
    else:
        # Return fallback data if API fails
        return {
            "value": 0,
            "change": 0,
            "change_percent": 0,
            "volume": "N/A",
            "last_update": datetime.now().strftime("%H:%M"),
            "error": "Could not fetch BIST 100 data"
        }

@app.get("/transactions", response_model=list[schemas.Transaction])
def read_transactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_transactions(db, skip=skip, limit=limit)

@app.post("/transactions", response_model=schemas.Transaction)
def create_transaction(tx: schemas.TransactionCreate, db: Session = Depends(get_db)):
    return crud.create_transaction(db, tx)

@app.post("/parse-message")
def parse_broker_message(payload: dict):
    message = payload.get("text", "")
    result = parse_message(message)
    if result:
        return result
    return {"error": "Mesaj tanınamadı"}

@router.post("/parse-and-log")
def parse_and_log(payload: dict, db: Session = Depends(get_db)):
    message = payload.get("text", "")
    result = parse_message(message)
    if not result:
        raise HTTPException(status_code=400, detail="Message could not be parsed.")

    tx = crud.create_transaction_from_message(db, result)
    return {
        "message": "Transaction created.",
        "parsed": result,
        "recorded": {
            "id": tx.id,
            "type": tx.type,
            "symbol": tx.symbol,
            "quantity": tx.quantity,
            "date": str(tx.date)
        }
    }

@app.get("/portfolio")
def get_portfolio(db: Session = Depends(get_db)):
    transactions = db.query(models.Transaction).all()

    # 📦 MOCK hisse fiyatları (daha sonra canlı veriyle değiştirilecek)
    mock_prices = {
        "SISE": 45.8,
        "THYAO": 102.3,
        "BIMAS": 245.6,
        "KCHOL": 160.2
    }

    result = calculate_portfolio_value(transactions, mock_prices)
    return result

@app.get("/portfolio/profit_loss", response_model=schemas.PortfolioAnalysis)
def get_profit_loss(db: Session = Depends(get_db)):
    transactions = db.query(models.Transaction).all()

    buy_total = defaultdict(float)
    sell_total = defaultdict(float)
    quantity = defaultdict(float)
    cash_invested = 0
    cash_returned = 0

    for tx in transactions:
        if tx.type == "buy":
            buy_total[tx.symbol] += tx.quantity * tx.price
            quantity[tx.symbol] += tx.quantity
        elif tx.type == "sell":
            sell_total[tx.symbol] += tx.quantity * tx.price
            quantity[tx.symbol] -= tx.quantity
        elif tx.type == "deposit":
            cash_invested += tx.quantity
        elif tx.type == "withdrawal":
            cash_returned += tx.quantity
        # Dividends are considered cash returned from investment
        elif tx.type == "dividend":
            cash_returned += tx.price # price field holds total dividend amount
        elif tx.type == 'split':
            # Splits increase quantity but don't affect cost basis directly
            quantity[tx.symbol] += tx.quantity

    holdings_data = []
    total_portfolio_value_try = 0
    total_portfolio_cost_try = 0

    for symbol, qty in quantity.items():
        if qty > 0:
            current_price = get_latest_price(symbol) or 0
            current_value = qty * current_price
            cost = buy_total[symbol] - sell_total[symbol]
            
            holdings_data.append({
                "symbol": symbol,
                "quantity": qty,
                "cost": round(cost, 2),
                "current_value": round(current_value, 2),
                "profit_loss": round(current_value - cost, 2),
                "current_price": round(current_price, 2)
            })
            total_portfolio_value_try += current_value
            total_portfolio_cost_try += cost

    # SADECE HİSSE DEĞERLERİ - cash flow dahil etmiyoruz
    # Net cash is what was put in minus what was taken out
    # net_cash_flow = cash_invested - cash_returned
    # total_portfolio_cost_try += net_cash_flow
    # total_portfolio_value_try += net_cash_flow

    # Fetch latest EUR rate and calculate EUR value
    latest_eur_rate = get_latest_eur_try_rate()
    total_portfolio_value_eur = (total_portfolio_value_try / latest_eur_rate) if latest_eur_rate else 0

    return {
        "holdings": holdings_data,
        "totals": {
            "total_value_try": round(total_portfolio_value_try, 2),
            "total_cost_try": round(total_portfolio_cost_try, 2),
            "total_profit_loss_try": round(total_portfolio_value_try - total_portfolio_cost_try, 2),
            "total_value_eur": round(total_portfolio_value_eur, 2)
        }
    }

@router.post("/events/add", status_code=201)
def add_event(payload: schemas.EventPayload, db: Session = Depends(get_db)):
    """
    Parses a financial event message (dividend or split), calculates its impact
    based on historical holdings, and logs it as a new transaction.
    """
    event_data = parse_event_message(payload.message)

    if not event_data:
        raise HTTPException(status_code=400, detail="Could not parse event message.")

    event_type = event_data["type"]
    symbol = event_data["symbol"]
    event_date = event_data["date"]

    shares_held = get_holdings_on_date(db, symbol, event_date)
    if shares_held <= 0:
        raise HTTPException(
            status_code=404,
            detail=f"No shares of {symbol} held on {event_date} to apply the event to."
        )

    if event_type == "dividend":
        total_dividend = shares_held * (event_data["percentage"] / 100.0)
        tx_schema = schemas.TransactionCreate(
            date=event_date, type='dividend', symbol=symbol,
            quantity=0, price=total_dividend, note=f"Dividend ({event_data['percentage']}%)"
        )
        created_tx = crud.create_transaction(db, tx_schema)
        return {"status": "success", "transaction": created_tx}

    if event_type == "split":
        new_shares = shares_held * (event_data["ratio"] - 1)
        tx_schema = schemas.TransactionCreate(
            date=event_date, type='split', symbol=symbol,
            quantity=new_shares, price=0, note=f"Stock Split ({event_data['ratio']}-for-1)"
        )
        created_tx = crud.create_transaction(db, tx_schema)
        return {"status": "success", "transaction": created_tx}
    
    # This should not be reached if parser is correct
    raise HTTPException(status_code=500, detail="Unhandled event type.")

# Data Export Endpoints
@app.get("/export/csv")
def export_csv(db: Session = Depends(get_db)):
    """
    Export all transactions to CSV format
    """
    try:
        csv_content = export_transactions_to_csv(db)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=transactions.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/export/excel")
def export_excel(db: Session = Depends(get_db)):
    """
    Export all transactions to Excel format with multiple sheets
    """
    try:
        excel_content = export_transactions_to_excel(db)
        return Response(
            content=excel_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=transactions.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/export/csv-template")
def get_csv_template():
    """
    Get a sample CSV template for import
    """
    try:
        template_content = create_sample_csv_template()
        return Response(
            content=template_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=import_template.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template generation failed: {str(e)}")

# Data Import Endpoints
@app.post("/import/csv")
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Import transactions from CSV file
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")
    
    try:
        content = await file.read()
        csv_content = content.decode('utf-8')
        result = import_transactions_from_csv(db, csv_content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@app.post("/import/excel")
async def import_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Import transactions from Excel file
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")
    
    try:
        content = await file.read()
        result = import_transactions_from_excel(db, content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

# Historical Data Analysis Endpoints
@app.get("/stocks/{symbol}/chart")
def get_stock_chart(symbol: str, period: str = "1y"):
    """
    Get detailed historical chart data for a single stock with technical indicators
    
    Parameters:
    - symbol: Stock symbol (e.g., 'SISE')
    - period: Time period ('1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
    """
    try:
        data = get_stock_historical_chart(symbol, period)
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chart data: {str(e)}")

@app.get("/analytics/portfolio-timeline")
def get_portfolio_timeline(db: Session = Depends(get_db)):
    """
    Get comprehensive portfolio timeline data with individual stock performance
    Only includes stocks currently held in portfolio
    """
    try:
        # Get date range from transactions
        transactions = db.query(models.Transaction).all()
        if not transactions:
            return {"error": "No transactions found"}
        
        start_date = min(tx.date for tx in transactions)
        end_date = datetime.now().date()
        
        data = get_portfolio_timeline_data(db, start_date, end_date)
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating timeline: {str(e)}")

@app.get("/analytics/market-comparison/{symbol}")
async def get_market_comparison(symbol: str, period: str = "1y", db: Session = Depends(get_db)):
    try:
        data = get_market_comparison_data(db, symbol, period)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/risk-metrics")
def get_portfolio_risk_metrics(db: Session = Depends(get_db), period: str = "1y"):
    """
    Calculate various risk metrics for portfolio stocks
    """
    try:
        data = get_risk_metrics(db, period)
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating risk metrics: {str(e)}")

@app.get("/portfolio/first-purchase-dates")
def get_first_purchase_dates(db: Session = Depends(get_db)):
    """
    Get the first purchase date for each stock symbol
    """
    try:
        # Get all buy transactions
        buy_transactions = db.query(models.Transaction).filter(
            models.Transaction.type == 'buy',
            models.Transaction.symbol.isnot(None)
        ).order_by(models.Transaction.date).all()
        
        first_purchases = {}
        for tx in buy_transactions:
            if tx.symbol not in first_purchases:
                first_purchases[tx.symbol] = tx.date.strftime("%Y-%m-%d")
        
        return first_purchases
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting first purchase dates: {str(e)}")

# New Enhanced Analytics Endpoints
@app.get("/analytics/sector-analysis")
def get_sector_allocation(db: Session = Depends(get_db)):
    """
    Get sector allocation and diversification analysis for current holdings
    """
    try:
        data = get_sector_analysis(db)
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating sector analysis: {str(e)}")

@app.get("/analytics/tax-report")
def get_tax_report(db: Session = Depends(get_db), year: int = None):
    """
    Get capital gains/losses tax report for specified year
    """
    try:
        data = get_tax_reporting_data(db, year)
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating tax report: {str(e)}")

@app.get("/analytics/dashboard-metrics")
def get_dashboard_analytics(db: Session = Depends(get_db)):
    """
    Get enhanced dashboard metrics including portfolio health, top performers, concentration risk
    """
    try:
        data = get_enhanced_dashboard_metrics(db)
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating dashboard metrics: {str(e)}")

@app.get("/portfolio/current-holdings")
def get_current_portfolio_holdings(db: Session = Depends(get_db)):
    """
    Get list of stocks currently held in portfolio with quantities
    """
    try:
        from backend.utils.portfolio_calculator import get_current_holdings_with_quantities
        holdings = get_current_holdings_with_quantities(db)
        return {"holdings": holdings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting current holdings: {str(e)}")