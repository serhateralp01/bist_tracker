# Complete Setup Guide for BIST Portfolio Tracker

This guide will walk you through setting up the BIST Portfolio Tracker on your machine step by step.

## 📋 Prerequisites Check

### 1. Install Python 3.8+

**Windows:**
1. Download Python from https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Verify: Open Command Prompt and run `python --version`

**macOS:**
```bash
# Using Homebrew (recommended)
brew install python3

# Or download from https://www.python.org/downloads/
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### 2. Install Node.js 16+

**Windows/macOS:**
- Download from https://nodejs.org/ (LTS version)

**Linux:**
```bash
# Using NodeSource repository
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 3. Install Git

**Windows:**
- Download from https://git-scm.com/

**macOS:**
```bash
brew install git
```

**Linux:**
```bash
sudo apt install git
```

## 🚀 Step-by-Step Setup

### Step 1: Clone the Repository

```bash
# Replace with your actual repository URL
git clone <your-repository-url>
cd hisse_takip
```

### Step 2: Backend Setup

#### Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# You should see (venv) in your terminal prompt
```

#### Install Backend Dependencies
```bash
# Install from root requirements file
pip install -r requirements.txt

# If the above fails, try:
pip install -r backend/requirements.txt
```

#### Verify Backend Installation
```bash
# Test if FastAPI is installed correctly
python -c "import fastapi; print('FastAPI installed successfully')"
```

### Step 3: Frontend Setup

#### Navigate to Frontend Directory
```bash
cd frontend
```

#### Install Frontend Dependencies
```bash
# Install all npm packages
npm install

# If you encounter errors, try:
npm install --legacy-peer-deps
```

#### Verify Frontend Installation
```bash
# Check if React is installed
npm list react
```

### Step 4: First Run

#### Terminal 1 - Start Backend
```bash
# Make sure you're in the project root directory
cd /path/to/hisse_takip

# Activate virtual environment (if not already active)
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Start the backend server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### Terminal 2 - Start Frontend
```bash
# Open a new terminal window/tab
cd /path/to/hisse_takip/frontend

# Start the React development server
npm start
```

You should see:
```
Compiled successfully!

You can now view frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

### Step 5: Verify Everything Works

1. **Backend API**: Open http://localhost:8000 in your browser
   - You should see: `{"message": "BIST Portfolio Tracker API"}`

2. **API Documentation**: Open http://localhost:8000/docs
   - You should see the FastAPI interactive documentation

3. **Frontend**: Open http://localhost:3000
   - You should see the React application dashboard

## 🔧 Configuration Options

### Environment Variables (Optional)

Create a `.env` file in the project root:

```env
# .env file
DATABASE_URL=sqlite:///./bist.db
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:3000
```

### Database Initialization

The SQLite database will be created automatically when you first run the backend. If you want to start fresh:

```bash
# Delete the database file (if it exists)
rm bist.db

# Restart the backend - it will create a new database
```

## 🎯 Testing the Setup

### Add a Test Transaction

1. Open http://localhost:3000
2. Go to "Transactions" page
3. Click "Add Transaction"
4. Fill in test data:
   - Type: Buy
   - Symbol: SISE
   - Quantity: 100
   - Price: 10.50
   - Date: Today's date
5. Click "Add Transaction"

### Parse a Test Message

1. Go to "Message Parse" page
2. Paste this test message:
   ```
   SISE hissesinden 50 adet 12.75 TL fiyattan alım işleminiz gerçekleşmiştir.
   ```
3. Click "Parse Message"
4. Verify the parsed data is correct

## 🐛 Common Setup Issues

### Python Issues

**"python is not recognized"**
- Add Python to your system PATH
- Use `python3` instead of `python` on macOS/Linux

**"No module named 'fastapi'"**
- Make sure virtual environment is activated
- Re-run `pip install -r requirements.txt`

### Node.js Issues

**"npm command not found"**
- Reinstall Node.js and make sure it's in your PATH

**"EACCES: permission denied"**
- On macOS/Linux, use: `sudo npm install -g npm`

**React compilation errors**
- Delete `node_modules` folder
- Delete `package-lock.json`
- Run `npm install` again

### Network Issues

**Backend not accessible**
- Check if port 8000 is free: `lsof -i :8000` (macOS/Linux)
- Try different port: `uvicorn backend.main:app --port 8001`

**Frontend not loading**
- Check if port 3000 is free
- Clear browser cache
- Try incognito mode

### Database Issues

**SQLite errors**
- Make sure you have write permissions in the project directory
- Delete `bist.db` and restart backend

## 📱 Next Steps

After successful setup:

1. **Explore the Dashboard** - View portfolio overview
2. **Add Real Transactions** - Input your actual stock transactions
3. **Test Message Parsing** - Try with real broker SMS messages
4. **Check Portfolio Analytics** - View charts and profit/loss analysis

## 🆘 Getting Help

If you encounter issues:

1. Check the terminal output for error messages
2. Verify all prerequisites are correctly installed
3. Make sure both backend and frontend are running
4. Check browser console for JavaScript errors (F12)
5. Review the logs in the terminal windows

## 🔄 Daily Usage

Once set up, to use the application daily:

1. **Start Backend**:
   ```bash
   cd hisse_takip
   source venv/bin/activate
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start Frontend**:
   ```bash
   cd hisse_takip/frontend
   npm start
   ```

3. Access at http://localhost:3000

Consider creating shell scripts or batch files to automate the startup process! 