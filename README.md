# BIST Portfolio Tracker

A modern, full-stack application designed to track and analyze your stock portfolio on Borsa Istanbul (BIST). Built with a FastAPI backend and a React frontend, it offers real-time data, transaction logging, and insightful performance visualizations.

![BIST Portfolio Tracker Demo](https://i.imgur.com/your-demo-image.gif)  <!-- Placeholder -->

## ✨ Key Features

- **Transaction Management**: Log all your trades, including buys, sells, dividends, and capital increases.
- **Automated Logging**: Automatically parse and record transactions from broker SMS notifications.
- **Real-Time Valuation**: View your portfolio's total value, updated with live stock prices from Yahoo Finance.
- **In-Depth Analytics**: Visualize your portfolio's daily performance, asset allocation, and profit/loss with interactive charts.
- **Responsive Design**: Access your portfolio on any device, with a clean and intuitive UI optimized for both desktop and mobile.
- **Secure & Private**: Your financial data is stored locally in a private SQLite database.

## 🛠️ Tech Stack

| Component  | Technology                                                                                                  |
|------------|-------------------------------------------------------------------------------------------------------------|
| **Backend**    | [Python](https://www.python.org/), [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy](https://www.sqlalchemy.org/), [Pydantic](https://docs.pydantic.dev/latest/) |
| **Frontend**   | [React](https://reactjs.org/), [TypeScript](https://www.typescriptlang.org/), [Tailwind CSS](https://tailwindcss.com/), [Recharts](https://recharts.org/)         |
| **Database**   | [SQLite](https://www.sqlite.org/index.html)                                                                 |
| **Data Source**| [yfinance](https://pypi.org/project/yfinance/) for live BIST stock data.                                     |

## 🚀 Getting Started

Follow these instructions to get the project up and running on your local machine.

### Prerequisites

- [Python 3.8+](https://www.python.org/downloads/)
- [Node.js v16+](https://nodejs.org/en/)
- `pip` and `npm` package managers

### Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/serhateralp01/bist_tracker.git
    cd bist_tracker
    ```

2.  **Setup the Backend**
    - Create and activate a virtual environment:
      ```bash
      python3 -m venv venv
      source venv/bin/activate
      ```
    - Install the required Python packages:
      ```bash
      pip install -r backend/requirements.txt
      ```

3.  **Setup the Frontend**
    - Navigate to the frontend directory and install npm packages:
      ```bash
      cd frontend
      npm install
      ```

### Running the Application

1.  **Start the Backend Server**
    - From the project root directory (`bist_tracker/`):
      ```bash
      uvicorn backend.main:app --reload
      ```
    - The backend API will be available at `http://127.0.0.1:8000`.

2.  **Start the Frontend Development Server**
    - In a new terminal, navigate to the `frontend` directory:
      ```bash
      cd frontend
      npm start
      ```
    - The application will open automatically in your browser at `http://localhost:3000`.

## Project Structure

The project is organized into two main folders: `backend` and `frontend`.

```
bist_tracker/
├── backend/
│   ├── crud.py           # Database CRUD operations
│   ├── database.py       # Database session and engine setup
│   ├── main.py           # FastAPI application and endpoints
│   ├── models.py         # SQLAlchemy ORM models
│   ├── schemas.py        # Pydantic data validation schemas
│   ├── requirements.txt  # Python dependencies
│   └── utils/            # Utility scripts (stock fetcher, parsers)
├── frontend/
│   ├── src/
│   │   ├── components/   # Reusable React components
│   │   ├── pages/        # Main pages for the application
│   │   └── services/     # API service for frontend-backend communication
│   ├── public/           # Static assets
│   └── package.json      # Node.js dependencies
├── .gitignore
└── README.md
```

---

*This project was bootstrapped with the help of a conversational AI pair programmer.* 