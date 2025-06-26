from pydantic import BaseModel
from datetime import date

class TransactionBase(BaseModel):
    type: str
    symbol: str
    quantity: float
    price: float
    date: date
    note: str = ""

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int

    model_config = {
    "from_attributes": True
}
