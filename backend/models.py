from sqlalchemy import Column, Integer, String, Float, Date
from backend.database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True)  # buy, sell, dividend, deposit, etc.
    symbol = Column(String, index=True)
    quantity = Column(Float)
    price = Column(Float)
    date = Column(Date)
    note = Column(String)
