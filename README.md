# 📈 BIST Stock Portfolio Tracker

A modern, full-stack application for tracking and analyzing your stock portfolio on Borsa Istanbul (BIST). Built with FastAPI backend and React frontend, featuring real-time data, advanced analytics, and intuitive portfolio management.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![React](https://img.shields.io/badge/react-19.1.0-blue.svg)
![FastAPI](https://img.shields.io/badge/fastapi-latest-green.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Key Features

### 💼 Portfolio Management
- **Transaction Management**: Log buys, sells, dividends, and capital increases
- **Real-Time Valuation**: Live stock prices from Yahoo Finance API
- **Multi-Currency Support**: TRY and USD tracking with real-time exchange rates
- **Performance Analytics**: 30-day gain/loss tracking in Turkish Lira
- **Risk Metrics**: Portfolio volatility and risk assessment

### 📱 Smart Message Parsing
- **SMS Integration**: Automatically parse broker SMS notifications (Garanti BBVA, İş Bankası, Yapı Kredi)
- **Bank Message Support**: Parse investment account statements
- **Auto-Detection**: Intelligent parsing of transaction details from messages

### 📊 Advanced Analytics
- **Dashboard Overview**: Portfolio summary with key metrics
- **Historical Performance**: Interactive charts with multiple time periods
- **Cash Flow Analysis**: Track money in/out of your portfolio
- **Sector Analysis**: Portfolio diversification insights
- **Profit/Loss Tracking**: Detailed P&L analysis per stock

### 🎨 Modern UI/UX
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Dark/Light Theme Support**: Tailwind CSS with modern design
- **Interactive Charts**: Recharts-powered data visualizations
- **Loading States**: Smooth animations and progress indicators
- **Enhanced Tooltips**: Detailed information on hover

### 🔧 Technical Features
- **Local Database**: Secure SQLite storage
- **Data Import/Export**: JSON-based portfolio backup/restore
- **Background Tasks**: Automated data fetching and updates
- **API Documentation**: Interactive Swagger/OpenAPI docs
- **Type Safety**: Full TypeScript implementation

## 🛠️ Tech Stack

### Backend
- **Python 3.8+** with FastAPI
- **SQLAlchemy** for ORM
- **SQLite** database
- **yfinance** for real-time stock data
- **APScheduler** for background tasks
- **Pydantic** for data validation

### Frontend
- **React 19** with TypeScript
- **Tailwind CSS** for styling
- **React Router** for navigation
- **Recharts** for data visualization
- **Axios** for API communication
- **Heroicons** for UI icons

## 🚀 Quick Start

### Prerequisites

Ensure you have the following installed:
- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Node.js 16+** - [Download](https://nodejs.org/)
- **Git** - [Download](https://git-scm.com/)

### One-Click Setup

For macOS/Linux users:
```bash
git clone https://github.com/serhateralp01/bist_tracker.git
cd hisse-takip
chmod +x setup.sh
./setup.sh
```

For Windows users:
```cmd
git clone https://github.com/serhateralp01/bist_tracker.git
cd hisse-takip
setup.bat
```

### Manual Setup

#### 1. Clone Repository
```bash
git clone https://github.com/serhateralp01/bist_tracker.git
cd hisse-takip
```

#### 2. Backend Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

### Running the Application

#### Option 1: Use Start Script (Recommended)
```bash
# macOS/Linux
./start.sh

# Windows
start.bat
```

#### Option 2: Manual Start
```bash
# Terminal 1 - Backend
python run_backend.py

# Terminal 2 - Frontend
cd frontend && npm start
```

### Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://127.0.0.1:8000
- **API Documentation**: http://127.0.0.1:8000/docs

## 📁 Project Architecture

```
hisse_takip/
├── 🔧 Backend (FastAPI)
│   ├── main.py              # Application entry point
│   ├── models.py            # Database models
│   ├── schemas.py           # Pydantic schemas
│   ├── crud.py              # Database operations
│   ├── database.py          # DB configuration
│   ├── scheduler.py         # Background tasks
│   └── utils/               # Utility modules
│       ├── stock_fetcher.py         # Real-time prices
│       ├── historical_fetcher.py    # Historical data & analytics
│       ├── message_parser.py        # SMS parsing
│       ├── portfolio_calculator.py  # Portfolio calculations
│       ├── currency_fetcher.py      # Exchange rates
│       ├── event_parser.py          # Corporate events
│       └── data_import_export.py    # Backup/restore
├── 🎨 Frontend (React)
│   ├── src/
│   │   ├── components/              # Reusable components
│   │   │   ├── BistStatus.tsx       # Market status
│   │   │   ├── InputTransaction.tsx # Transaction form
│   │   │   ├── LoadingSpinner.tsx   # Loading animations
│   │   │   ├── Navigation.tsx       # App navigation
│   │   │   ├── PortfolioChart.tsx   # Chart component
│   │   │   ├── StatCard.tsx         # Metric cards
│   │   │   ├── EnhancedTooltip.tsx  # Custom tooltips
│   │   │   └── ImportExport.tsx     # Data management
│   │   ├── pages/                   # Application pages
│   │   │   ├── Dashboard.tsx        # Main dashboard
│   │   │   ├── Analytics.tsx        # Advanced analytics
│   │   │   ├── Transactions.tsx     # Transaction management
│   │   │   ├── CashFlow.tsx         # Cash flow analysis
│   │   │   └── MessageParse.tsx     # SMS parsing
│   │   ├── services/
│   │   │   └── api.ts               # API client
│   │   └── App.tsx                  # Main component
├── 📊 Database
│   └── bist.db                      # SQLite database
├── 🔧 Configuration
│   ├── requirements.txt             # Python dependencies
│   ├── run_backend.py              # Backend runner
│   ├── start.sh / start.bat        # Launch scripts
│   └── setup.sh / setup.bat        # Setup scripts
└── 📚 Documentation
    ├── README.md                    # This file
    └── SETUP.md                     # Detailed setup guide
```

## 📖 Feature Documentation

### 🎯 Dashboard
- **Portfolio Summary**: Total value, daily change, 30-day performance
- **Stock Holdings**: Individual stock performance with real-time prices
- **Risk Metrics**: Portfolio volatility and risk assessment
- **Interactive Charts**: Historical performance visualization

### 📈 Analytics Page
- **Performance Charts**: Multiple timeframe analysis (1D, 1W, 1M, 3M, 6M, 1Y)
- **Sector Distribution**: Portfolio allocation by sector
- **Top Performers**: Best and worst performing stocks
- **Historical Trends**: Long-term performance analysis

### 💰 Cash Flow Analysis
- **Money Flow Tracking**: Deposits and withdrawals
- **Investment Timeline**: Transaction history visualization
- **Return Calculations**: Investment performance metrics

### 📱 Message Parsing
- **Supported Banks**: Garanti BBVA, İş Bankası, Yapı Kredi
- **Auto-Detection**: Automatic transaction type recognition
- **Smart Parsing**: Extract symbols, quantities, prices, and dates
- **Manual Review**: Confirm before adding to portfolio

### 💾 Data Management
- **Export Portfolio**: JSON backup of all data
- **Import Data**: Restore from backup files
- **Transaction History**: Complete audit trail
- **Data Validation**: Ensure data integrity

## 🔌 API Reference

### Authentication
Currently using simple CORS setup. Future versions will include proper authentication.

### Core Endpoints

#### Transactions
```http
GET    /transactions              # List all transactions
POST   /transactions              # Create transaction
PUT    /transactions/{id}         # Update transaction
DELETE /transactions/{id}         # Delete transaction
```

#### Portfolio
```http
GET    /portfolio/summary         # Portfolio overview
GET    /portfolio/daily_value     # Daily values
GET    /portfolio/profit_loss     # P&L analysis
GET    /portfolio/holdings        # Current holdings
```

#### Market Data
```http
GET    /market/prices            # Current stock prices
GET    /market/status            # Market status
GET    /market/historical        # Historical data
```

#### Utilities
```http
POST   /parse-message            # Parse SMS messages
GET    /health                   # Health check
POST   /export                   # Export data
POST   /import                   # Import data
```

## 🎮 Usage Guide

### Adding Transactions

1. **Manual Entry**:
   - Navigate to **Transactions** page
   - Click **"Add Transaction"**
   - Fill in details (type, symbol, quantity, price, date)
   - Click **"Save"**

2. **SMS Parsing**:
   - Go to **Message Parse** page
   - Paste broker SMS
   - Review parsed details
   - Confirm to add

### Viewing Analytics

1. **Dashboard Overview**:
   - Quick portfolio summary
   - Recent performance
   - Key metrics at a glance

2. **Detailed Analytics**:
   - Navigate to **Analytics** page
   - Select time period
   - Explore charts and metrics
   - Analyze performance trends

### Data Management

1. **Export Data**:
   - Use **Import/Export** component
   - Download JSON backup
   - Store safely

2. **Import Data**:
   - Select backup file
   - Review data
   - Confirm import

## 🐛 Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Solution 1: Check Python path
python --version  # Should be 3.8+
which python

# Solution 2: Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Solution 3: Use run_backend.py
python run_backend.py
```

#### Frontend Issues
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 16+
```

#### Database Problems
```bash
# Reset database
rm bist.db
# Restart application - database will be recreated
```

#### Stock Data Not Loading
- Check internet connection
- Verify stock symbols (use BIST format: SISE, THYAO, etc.)
- Some stocks may not be available on Yahoo Finance

### Getting Help

1. **Check Logs**: Look at terminal output for error messages
2. **API Docs**: Visit http://127.0.0.1:8000/docs when backend is running
3. **Browser Console**: Check for frontend errors
4. **GitHub Issues**: Report bugs or request features

## 🚧 Development

### Setting Up Development Environment

```bash
# Install development dependencies
pip install -r requirements.txt

# Frontend development server
cd frontend
npm start

# Backend with auto-reload
python run_backend.py
```

### Code Structure Guidelines

- **Backend**: Follow FastAPI best practices
- **Frontend**: Use TypeScript for type safety
- **Styling**: Tailwind CSS with component-based approach
- **State Management**: React hooks and context
- **API Calls**: Centralized in `services/api.ts`

### Testing

```bash
# Frontend tests
cd frontend
npm test

# Backend tests (when available)
pytest backend/tests/
```

## 📊 Database Schema

### Core Tables

**Transactions**
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type VARCHAR(20) NOT NULL,        -- 'buy', 'sell', 'dividend', 'capital_increase', 'deposit'
    symbol VARCHAR(10),               -- Stock symbol (nullable for deposits)
    quantity FLOAT,                   -- Number of shares
    price FLOAT,                     -- Price per share
    date DATE NOT NULL,              -- Transaction date
    note TEXT,                       -- Additional notes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Daily Values** (Auto-generated)
```sql
CREATE TABLE daily_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    total_value_try FLOAT,
    total_value_usd FLOAT,
    daily_change_try FLOAT,
    daily_change_percent FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔄 Version History

### v1.0.0 (Current)
- ✅ Complete portfolio tracking system
- ✅ Advanced analytics dashboard
- ✅ SMS message parsing for major banks
- ✅ Real-time stock price integration
- ✅ Modern React UI with TypeScript
- ✅ Data import/export functionality
- ✅ Responsive design
- ✅ 30-day TRY gain/loss tracking
- ✅ Enhanced loading states and animations

### Upcoming Features
- 🔄 User authentication system
- 🔄 Multi-user support
- 🔄 Email notifications
- 🔄 Mobile app (React Native)
- 🔄 Advanced reporting
- 🔄 API rate limiting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

### Development Guidelines
- Follow existing code style
- Add tests for new features
- Update documentation
- Test thoroughly before submitting

## 🙏 Acknowledgments

- **Yahoo Finance** for providing stock data
- **FastAPI** community for excellent documentation
- **React** team for the amazing framework
- **Tailwind CSS** for beautiful styling utilities
- **BIST** investors community for feedback and suggestions

## 📞 Support

- **Documentation**: Check this README and `/docs` endpoint
- **Issues**: [GitHub Issues](https://github.com/serhateralp01/bist_tracker/issues)
---

<div align="center">

*Making portfolio tracking simple, powerful, and accessible to everyone*

[⭐ Star this project](https://github.com/serhateralp01/bist_tracker) | [🐛 Report Bug](https://github.com/serhateralp01/bist_tracker/issues) | [💡 Request Feature](https://github.com/serhateralp01/bist_tracker/issues)

</div> 