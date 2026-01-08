# BIST Stock Portfolio Tracker

## Features
- **Portfolio Tracking**: Track your BIST stocks, calculate costs (FIFO), and monitor profit/loss.
- **Transactions**: Add, edit, delete, import (CSV), and export (CSV) transactions.
- **Dashboard**: View portfolio health, top performers, and concentration risk.
- **Analysis & Forecasting**:
    - Interactive charts powered by Plotly.
    - Time series forecasting using Holt-Winters Exponential Smoothing.
- **Technology Stack**: Flask, SQLAlchemy, Pandas, Statsmodels, Plotly.

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python run.py
   ```
3. Open your browser at `http://localhost:8000`.

## Testing
Run tests with pytest:
```bash
python -m pytest tests/
```
