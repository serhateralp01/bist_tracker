from pydantic import BaseModel
from datetime import date
from typing import List, Optional

# Base schema for a transaction
class TransactionBase(BaseModel):
    date: date
    type: str
    quantity: float
    symbol: Optional[str] = None
    price: Optional[float] = None
    note: Optional[str] = ""

# Schema for creating a transaction
class TransactionCreate(TransactionBase):
    pass

# Schema for reading a transaction (includes all fields from DB)
class Transaction(TransactionBase):
    id: int
    exchange_rate: Optional[float] = None
    value_eur: Optional[float] = None

    class Config:
        from_attributes = True

# Schema for individual profit/loss records
class ProfitLoss(BaseModel):
    symbol: str
    quantity: float
    cost: float
    current_value: float
    profit_loss: float
    current_price: float

# Schema for the overall portfolio analysis endpoint
class PortfolioAnalysis(BaseModel):
    holdings: List[ProfitLoss]
    totals: dict

# Schema for the daily portfolio value chart
class PortfolioValue(BaseModel):
    date: str
    value_try: float
    value_eur: float
