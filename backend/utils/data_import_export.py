import pandas as pd
import io
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from backend import models, schemas
from backend.utils.currency_fetcher import get_historical_eur_try_rate

def export_transactions_to_csv(db: Session) -> str:
    """
    Export all transactions to CSV format
    Returns CSV string
    """
    transactions = db.query(models.Transaction).order_by(models.Transaction.date).all()
    
    data = []
    for tx in transactions:
        data.append({
            'date': tx.date.strftime('%Y-%m-%d'),
            'type': tx.type,
            'symbol': tx.symbol or '',
            'quantity': tx.quantity or 0,
            'price': tx.price or 0,
            'total_value_try': (tx.quantity or 0) * (tx.price or 0) if tx.type in ['buy', 'sell'] else (tx.price or 0),
            'exchange_rate_eur_try': tx.exchange_rate or '',
            'value_eur': tx.value_eur or '',
            'note': tx.note or ''
        })
    
    df = pd.DataFrame(data)
    return df.to_csv(index=False)

def export_transactions_to_excel(db: Session) -> bytes:
    """
    Export all transactions to Excel format with multiple sheets
    Returns Excel file as bytes
    """
    transactions = db.query(models.Transaction).order_by(models.Transaction.date).all()
    
    # Prepare data for transactions sheet
    tx_data = []
    for tx in transactions:
        tx_data.append({
            'Date': tx.date.strftime('%Y-%m-%d'),
            'Type': tx.type,
            'Symbol': tx.symbol or '',
            'Quantity': tx.quantity or 0,
            'Price (TRY)': tx.price or 0,
            'Total Value (TRY)': (tx.quantity or 0) * (tx.price or 0) if tx.type in ['buy', 'sell'] else (tx.price or 0),
            'EUR/TRY Rate': tx.exchange_rate or '',
            'Value (EUR)': tx.value_eur or '',
            'Note': tx.note or ''
        })
    
    # Create summary data
    summary_data = _create_summary_data(transactions)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Transactions sheet
        df_transactions = pd.DataFrame(tx_data)
        df_transactions.to_excel(writer, sheet_name='Transactions', index=False)
        
        # Summary sheet
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        # Holdings sheet
        holdings_data = _create_holdings_data(transactions)
        df_holdings = pd.DataFrame(holdings_data)
        df_holdings.to_excel(writer, sheet_name='Current Holdings', index=False)
    
    output.seek(0)
    return output.read()

def import_transactions_from_csv(db: Session, csv_content: str) -> Dict[str, Any]:
    """
    Import transactions from CSV content
    Returns result with success/error information
    """
    try:
        # Read CSV
        df = pd.read_csv(io.StringIO(csv_content))
        
        # Validate required columns
        required_columns = ['date', 'type', 'quantity', 'price']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return {
                'success': False,
                'error': f'Missing required columns: {", ".join(missing_columns)}',
                'imported_count': 0
            }
        
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Parse and validate data
                transaction_data = _parse_transaction_row(row)
                
                # Create transaction
                _create_transaction_with_exchange_rate(db, transaction_data)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
                continue
        
        db.commit()
        
        return {
            'success': True,
            'imported_count': imported_count,
            'errors': errors
        }
        
    except Exception as e:
        db.rollback()
        return {
            'success': False,
            'error': str(e),
            'imported_count': 0
        }

def import_transactions_from_excel(db: Session, excel_content: bytes) -> Dict[str, Any]:
    """
    Import transactions from Excel file
    Returns result with success/error information
    """
    try:
        # Read Excel file
        df = pd.read_excel(io.BytesIO(excel_content), sheet_name=0)  # First sheet
        
        # Convert to CSV-like format and use CSV import logic
        csv_content = df.to_csv(index=False)
        return import_transactions_from_csv(db, csv_content)
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error reading Excel file: {str(e)}',
            'imported_count': 0
        }

def _parse_transaction_row(row: pd.Series) -> Dict[str, Any]:
    """
    Parse a row of transaction data and validate it
    """
    # Parse date
    try:
        if pd.isna(row['date']):
            raise ValueError("Date is required")
        transaction_date = pd.to_datetime(row['date']).date()
    except:
        raise ValueError(f"Invalid date format: {row['date']}")
    
    # Parse type
    transaction_type = str(row['type']).lower().strip()
    valid_types = ['buy', 'sell', 'deposit', 'withdrawal', 'dividend', 'capital_increase', 'split']
    if transaction_type not in valid_types:
        raise ValueError(f"Invalid transaction type: {transaction_type}. Must be one of: {', '.join(valid_types)}")
    
    # Parse symbol (optional for deposits/withdrawals)
    symbol = None
    if not pd.isna(row.get('symbol', '')):
        symbol = str(row['symbol']).upper().strip()
        if len(symbol) == 0:
            symbol = None
    
    # Parse quantity
    try:
        quantity = float(row['quantity']) if not pd.isna(row['quantity']) else 0
    except:
        raise ValueError(f"Invalid quantity: {row['quantity']}")
    
    # Parse price
    try:
        price = float(row['price']) if not pd.isna(row['price']) else 0
    except:
        raise ValueError(f"Invalid price: {row['price']}")
    
    # Parse note
    note = str(row.get('note', '')) if not pd.isna(row.get('note', '')) else None
    if note == '':
        note = None
    
    # Validate business rules
    if transaction_type in ['buy', 'sell'] and not symbol:
        raise ValueError("Symbol is required for buy/sell transactions")
    
    if transaction_type in ['buy', 'sell'] and (quantity <= 0 or price <= 0):
        raise ValueError("Quantity and price must be positive for buy/sell transactions")
    
    if transaction_type in ['deposit', 'withdrawal'] and quantity <= 0:
        raise ValueError("Amount must be positive for deposits/withdrawals")
    
    return {
        'date': transaction_date,
        'type': transaction_type,
        'symbol': symbol,
        'quantity': quantity,
        'price': price,
        'note': note
    }

def _create_transaction_with_exchange_rate(db: Session, transaction_data: Dict[str, Any]):
    """
    Create a transaction with automatic exchange rate calculation
    """
    # Fetch historical EUR/TRY rate
    exchange_rate = get_historical_eur_try_rate(transaction_data['date'])
    value_eur = None
    
    if exchange_rate and transaction_data.get('price') and transaction_data.get('quantity'):
        if transaction_data['type'] in ["buy", "sell"]:
            value_eur = (transaction_data['price'] * transaction_data['quantity']) / exchange_rate
        elif transaction_data['type'] == "dividend":
            value_eur = transaction_data['price'] / exchange_rate
    
    db_tx = models.Transaction(
        **transaction_data,
        exchange_rate=exchange_rate,
        value_eur=value_eur
    )
    db.add(db_tx)

def _create_summary_data(transactions: List[models.Transaction]) -> List[Dict[str, Any]]:
    """
    Create summary statistics from transactions
    """
    summary = []
    
    # Group by type
    from collections import defaultdict
    type_counts = defaultdict(int)
    type_values = defaultdict(float)
    
    for tx in transactions:
        type_counts[tx.type] += 1
        if tx.type in ['buy', 'sell'] and tx.price and tx.quantity:
            type_values[tx.type] += tx.price * tx.quantity
        elif tx.type in ['dividend', 'deposit', 'withdrawal'] and tx.price:
            type_values[tx.type] += tx.price
    
    for tx_type, count in type_counts.items():
        summary.append({
            'Transaction Type': tx_type.title(),
            'Count': count,
            'Total Value (TRY)': round(type_values[tx_type], 2)
        })
    
    return summary

def _create_holdings_data(transactions: List[models.Transaction]) -> List[Dict[str, Any]]:
    """
    Create current holdings summary
    """
    from collections import defaultdict
    holdings = defaultdict(float)
    
    for tx in transactions:
        if tx.symbol and tx.quantity:
            if tx.type == 'buy':
                holdings[tx.symbol] += tx.quantity
            elif tx.type == 'sell':
                holdings[tx.symbol] -= tx.quantity
            elif tx.type == 'split':
                holdings[tx.symbol] += tx.quantity
    
    holdings_data = []
    for symbol, quantity in holdings.items():
        if quantity > 0:
            holdings_data.append({
                'Symbol': symbol,
                'Quantity': quantity
            })
    
    return holdings_data

def create_sample_csv_template() -> str:
    """
    Create a sample CSV template for users to follow
    """
    sample_data = [
        {
            'date': '2024-01-15',
            'type': 'deposit',
            'symbol': '',
            'quantity': 5000,
            'price': 1,
            'note': 'Initial deposit'
        },
        {
            'date': '2024-01-16',
            'type': 'buy',
            'symbol': 'SISE',
            'quantity': 100,
            'price': 12.50,
            'note': 'First SISE purchase'
        },
        {
            'date': '2024-01-20',
            'type': 'dividend',
            'symbol': 'SISE',
            'quantity': 0,
            'price': 25.00,
            'note': 'Q4 dividend payment'
        }
    ]
    
    df = pd.DataFrame(sample_data)
    return df.to_csv(index=False) 