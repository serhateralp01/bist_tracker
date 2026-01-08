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
    asset_type: Optional[str] = "STOCK"
    currency: Optional[str] = "TRY"

# Schema for reading a transaction (includes all fields from DB)
class Transaction(TransactionBase):
    id: int
    exchange_rate: Optional[float] = None
    value_eur: Optional[float] = None
    asset_type: Optional[str] = "STOCK"
    currency: Optional[str] = "TRY"

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
    average_purchase_price: Optional[float] = 0
    return_percentage: Optional[float] = 0

class PortfolioTotals(BaseModel):
    total_value_try: float
    total_cost_try: float
    total_profit_loss_try: float
    total_value_usd: float
    total_value_eur: float

# Schema for the overall portfolio analysis endpoint
class PortfolioAnalysis(BaseModel):
    holdings: List[ProfitLoss]
    totals: PortfolioTotals

# Schema for the daily portfolio value chart
class PortfolioValue(BaseModel):
    date: str
    value_try: float
    value_usd: float
    value_eur: float

class EventPayload(BaseModel):
    message: str
