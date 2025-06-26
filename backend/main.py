from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from backend import models, schemas, crud
from backend.database import SessionLocal, engine
from backend.utils.message_parser import parse_message
from backend.utils.portfolio_calculator import calculate_portfolio_value
from fastapi import APIRouter
from collections import defaultdict
from datetime import datetime, timedelta
from backend.schemas import Transaction
from backend.utils.stock_fetcher import get_latest_price


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

router = APIRouter()

@router.get("/portfolio/daily_value")
def get_daily_portfolio_value():
    db = SessionLocal()
    transactions = db.query(models.Transaction).order_by(models.Transaction.date).all()

    holdings = defaultdict(float)
    cash = 0
    portfolio_value_by_day = []

    if not transactions:
        return []

    current_day = transactions[0].date
    end_day = datetime.now().date()
    tx_index = 0

    def fetch_price(symbol):
        return get_latest_price(symbol) or 0

    while current_day <= end_day:
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
            tx_index += 1

        total = cash
        for symbol, qty in holdings.items():
            total += qty * fetch_price(symbol)

        portfolio_value_by_day.append({
            "date": str(current_day),
            "value": round(total, 2)
        })

        current_day += timedelta(days=1)

    return portfolio_value_by_day

app.include_router(router)

# DB bağımlılığı
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "BIST Portfolio Tracker Backend is running."}

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

@app.post("/parse-and-log")
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

@app.get("/portfolio/profit_loss")
def get_profit_loss(db: Session = Depends(get_db)):
    transactions = db.query(models.Transaction).all()

    buy_total = defaultdict(float)
    sell_total = defaultdict(float)
    quantity = defaultdict(float)

    for tx in transactions:
        if tx.type == "buy":
            buy_total[tx.symbol] += tx.quantity * tx.price
            quantity[tx.symbol] += tx.quantity
        elif tx.type == "sell":
            sell_total[tx.symbol] += tx.quantity * tx.price
            quantity[tx.symbol] -= tx.quantity

    result = []
    for symbol, qty in quantity.items():
        current_price = get_latest_price(symbol) or 0
        current_value = qty * current_price
        cost = buy_total[symbol] - sell_total[symbol]
        result.append({
            "symbol": symbol,
            "quantity": qty,
            "cost": round(cost, 2),
            "current_value": round(current_value, 2),
            "profit_loss": round(current_value - cost, 2),
            "current_price": round(current_price, 2)
        })

    return result