from app import db

class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True, index=True)
    type = db.Column(db.String, index=True)  # buy, sell, dividend, deposit, etc.
    symbol = db.Column(db.String, index=True, nullable=True)
    quantity = db.Column(db.Float)
    price = db.Column(db.Float, nullable=True)
    date = db.Column(db.Date)
    exchange_rate = db.Column(db.Float, nullable=True)
    value_eur = db.Column(db.Float, nullable=True)
    note = db.Column(db.String)

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'price': self.price,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'exchange_rate': self.exchange_rate,
            'value_eur': self.value_eur,
            'note': self.note
        }
