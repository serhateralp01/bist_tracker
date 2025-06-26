from collections import defaultdict
from sqlalchemy.orm import Session
from fastapi import Depends
from backend import models, schemas, crud
from datetime import date

def get_transactions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Transaction).offset(skip).limit(limit).all()

def create_transaction(db: Session, transaction: schemas.TransactionCreate):
    db_transaction = models.Transaction(
        type=transaction.type,
        symbol=transaction.symbol,
        quantity=transaction.quantity,
        price=transaction.price,
        date=transaction.date,
        note=transaction.note,
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def create_transaction_from_message(db: Session, parsed_msg: dict):
    tx = models.Transaction(
        type=parsed_msg["type"],
        symbol=parsed_msg["symbol"],
        quantity=parsed_msg.get("rate", 0),
        price=0,
        date=date.today(),
        note=f"AUTO from message: {parsed_msg.get('kind', parsed_msg['type'])}"
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx

def add_transaction(db: Session, transaction: schemas.TransactionCreate):
    return create_transaction(db, transaction)
