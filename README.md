# BIST Stock Portfolio Tracker

A modern, full-stack application for tracking and analyzing your stock portfolio on Borsa Istanbul (BIST). Built with FastAPI backend and React frontend, featuring real-time data, transaction management, and portfolio analytics.

## ✨ Features

- **Transaction Management**: Log buys, sells, dividends, and capital increases
- **SMS Message Parsing**: Automatically parse broker SMS notifications
- **Real-Time Portfolio Valuation**: Live stock prices from Yahoo Finance
- **Portfolio Analytics**: Daily performance charts and profit/loss analysis
- **Responsive Design**: Works on desktop and mobile devices
- **Local Data Storage**: Secure SQLite database

## 🛠️ Tech Stack

**Backend:**
- Python 3.8+
- FastAPI
- SQLAlchemy
- yfinance for stock data
- SQLite database

**Frontend:**
- React 18
- TypeScript
- Tailwind CSS
- Recharts for data visualization
- Axios for API calls

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8 or higher** - [Download Python](https://www.python.org/downloads/)
- **Node.js 16 or higher** - [Download Node.js](https://nodejs.org/)
- **Git** - [Download Git](https://git-scm.com/)

### Verify Installation

```bash
python --version    # Should be 3.8+
node --version      # Should be 16+
npm --version       # Should be 8+
```

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd hisse_takip
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install Python dependencies
pip install -r backend/requirements.txt
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Return to project root
cd ..
```

### 4. Run the Application

**Terminal 1 - Backend:**
```bash
# Make sure you're in the project root and virtual environment is activated
source venv/bin/activate  # Skip if already activated
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📁 Project Structure

```
hisse_takip/
├── backend/                    # FastAPI backend
│   ├── main.py                # FastAPI application entry point
│   ├── models.py              # SQLAlchemy database models
│   ├── schemas.py             # Pydantic data schemas
│   ├── crud.py                # Database CRUD operations
│   ├── database.py            # Database configuration
│   ├── scheduler.py           # Background tasks
│   ├── requirements.txt       # Python dependencies
│   └── utils/                 # Utility modules
│       ├── stock_fetcher.py   # Real-time stock price fetching
│       ├── message_parser.py  # SMS message parsing
│       ├── portfolio_calculator.py  # Portfolio calculations
│       ├── currency_fetcher.py      # Currency exchange rates
│       ├── historical_fetcher.py    # Historical data
│       └── event_parser.py          # Corporate events parsing
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # Reusable React components
│   │   │   ├── BistStatus.tsx
│   │   │   ├── InputTransaction.tsx
│   │   │   ├── Navigation.tsx
│   │   │   ├── PortfolioChart.tsx
│   │   │   └── StatCard.tsx
│   │   ├── pages/            # Application pages
│   │   │   ├── Dashboard.tsx
│   │   │   ├── MessageParse.tsx
│   │   │   └── Transactions.tsx
│   │   ├── services/         # API service layer
│   │   │   └── api.ts
│   │   └── App.tsx           # Main application component
│   ├── public/               # Static assets
│   ├── package.json          # Node.js dependencies
│   └── tailwind.config.js    # Tailwind CSS configuration
├── venv/                     # Python virtual environment
├── bist.db                   # SQLite database (created automatically)
├── requirements.txt          # Root requirements file
└── README.md
```

## 🔧 Configuration

### Environment Variables (Optional)

Create a `.env` file in the project root for custom configuration:

```env
# Database
DATABASE_URL=sqlite:///./bist.db

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000
```

## 📖 API Endpoints

### Transactions
- `GET /transactions` - Get all transactions
- `POST /transactions` - Create new transaction
- `PUT /transactions/{id}` - Update transaction
- `DELETE /transactions/{id}` - Delete transaction

### Portfolio
- `GET /portfolio/daily_value` - Get daily portfolio values
- `GET /portfolio/profit_loss` - Get profit/loss analysis

### Message Parsing
- `POST /parse-message` - Parse broker SMS messages

### Health Check
- `GET /` - API health check

## 🎯 Usage Examples

### Adding a Transaction

1. Go to **Transactions** page
2. Click **"Add Transaction"**
3. Fill in the details:
   - Type: Buy/Sell/Dividend/Capital Increase
   - Symbol: Stock symbol (e.g., SISE, THYAO)
   - Quantity: Number of shares
   - Price: Price per share
   - Date: Transaction date

### Parsing SMS Messages

1. Go to **Message Parse** page
2. Paste your broker SMS message
3. Click **"Parse Message"**
4. Review and confirm the parsed transaction

### Viewing Portfolio Analytics

1. Go to **Dashboard** page
2. View your portfolio summary cards
3. Analyze performance with interactive charts
4. Check profit/loss for individual stocks

## 🛠️ Development

### Backend Development

```bash
# Install development dependencies
pip install -r backend/requirements.txt

# Run with auto-reload
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Run tests (if available)
pytest backend/tests/
```

### Frontend Development

```bash
cd frontend

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

## 🐛 Troubleshooting

### Common Issues

**1. ModuleNotFoundError: No module named 'backend'**
- Make sure you're running uvicorn from the project root directory
- Ensure virtual environment is activated

**2. Cannot connect to backend from frontend**
- Check if backend is running on http://localhost:8000
- Verify CORS settings in backend/main.py

**3. Stock data not loading**
- Check internet connection
- Some stocks might not be available on Yahoo Finance
- Try with different stock symbols (e.g., SISE.IS, THYAO.IS)

**4. Database errors**
- Delete `bist.db` file and restart the application
- Check file permissions

**5. npm install fails**
- Try deleting `node_modules` and `package-lock.json`, then run `npm install` again
- Update Node.js to the latest LTS version

### Getting Help

1. Check the [API documentation](http://localhost:8000/docs) when backend is running
2. Look at browser console for frontend errors
3. Check terminal outputs for backend errors

## 🔄 Database Schema

### Transactions Table
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type VARCHAR(20) NOT NULL,  -- 'buy', 'sell', 'dividend', 'capital_increase', 'deposit'
    symbol VARCHAR(10),         -- Stock symbol (nullable for deposits)
    quantity FLOAT,             -- Number of shares
    price FLOAT,               -- Price per share
    date DATE NOT NULL,        -- Transaction date
    note TEXT                  -- Additional notes
);
```

## 📄 License

This project is open source. Feel free to use, modify, and distribute as needed.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

Built with ❤️ for BIST investors 