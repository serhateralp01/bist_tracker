from sqlalchemy import Column, Integer, String, Float, Date
from backend.database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True)  # buy, sell, dividend, deposit, etc.
    symbol = Column(String, index=True, nullable=True)
    quantity = Column(Float)
    price = Column(Float, nullable=True)
    date = Column(Date)
    exchange_rate = Column(Float, nullable=True)
    value_eur = Column(Float, nullable=True)
    note = Column(String)
