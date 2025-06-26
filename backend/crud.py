from collections import defaultdict
from sqlalchemy.orm import Session
from fastapi import Depends
from backend import models, schemas, crud
from datetime import date
from .utils.currency_fetcher import get_historical_eur_try_rate

def get_transactions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Transaction).offset(skip).limit(limit).all()

def create_transaction(db: Session, tx: schemas.TransactionCreate):
    # Fetch historical EUR/TRY rate
    exchange_rate = get_historical_eur_try_rate(tx.date)
    value_eur = None

    if exchange_rate and tx.price and tx.quantity:
        # Calculate value in EUR for buy/sell transactions
        if tx.type in ["buy", "sell"]:
            value_eur = (tx.price * tx.quantity) / exchange_rate
        # For dividends, the 'price' is the total amount
        elif tx.type == "dividend":
            value_eur = tx.price / exchange_rate

    db_tx = models.Transaction(
        **tx.model_dump(),
        exchange_rate=exchange_rate,
        value_eur=value_eur
    )
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)
    return db_tx

def create_transaction_from_message(db: Session, parsed_data: dict):
    # Fetch historical EUR/TRY rate
    exchange_rate = get_historical_eur_try_rate(parsed_data['date'])
    value_eur = None

    if exchange_rate and parsed_data.get('price') and parsed_data.get('quantity'):
        if parsed_data['type'] in ["buy", "sell"]:
             value_eur = (parsed_data['price'] * parsed_data['quantity']) / exchange_rate
        elif parsed_data['type'] == "dividend":
             value_eur = parsed_data['price'] / exchange_rate
    
    db_tx = models.Transaction(
        **parsed_data,
        exchange_rate=exchange_rate,
        value_eur=value_eur
    )
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)
    return db_tx

def add_transaction(db: Session, transaction: schemas.TransactionCreate):
    return create_transaction(db, transaction)
