# TeleManager Backend

Real Telegram account management API powered by **FastAPI** and **Telethon**.

## 🚀 Quick Start

### Option 1: Using the run script
```bash
cd backend
python run.py
```

### Option 2: Manual setup
```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

## 📡 API Endpoints

### Health Check
- `GET /` - Service info
- `GET /api/health` - Health check

### Authentication Flow
1. `POST /api/auth/send-code` - Send OTP to phone
   ```json
   {
     "phone": "+1234567890",
     "api_id": "your_api_id",
     "api_hash": "your_api_hash"
   }
   ```

2. `POST /api/auth/verify-code` - Verify OTP
   ```json
   {
     "phone": "+1234567890",
     "code": "12345"
   }
   ```

3. `POST /api/auth/verify-2fa` - Verify 2FA password (if required)
   ```json
   {
     "phone": "+1234567890",
     "password": "your_2fa_password"
   }
   ```

### Account Management
- `GET /api/accounts` - List all accounts
- `GET /api/accounts/{id}` - Get account details
- `GET /api/accounts/{id}/status` - Check session validity
- `DELETE /api/accounts/{id}` - Logout & remove account

## 📁 Project Structure

```
backend/
├── main.py              # FastAPI app & routes
├── telegram_manager.py  # Telethon client management
├── database.py          # SQLite database operations
├── config.py            # Configuration
├── requirements.txt     # Python dependencies
├── run.py              # Quick start script
├── sessions/           # Telethon session files
└── data/               # SQLite database
```

## 🔐 Getting API Credentials

1. Go to [my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Click "API development tools"
4. Create a new application
5. Copy the `api_id` and `api_hash`

## ⚠️ Important Notes

- Session files in `./sessions/` contain your login credentials - keep them safe!
- The API allows managing multiple Telegram accounts
- Each account's session is stored separately
- Never share your `api_hash` publicly

## 🛠️ Configuration

Copy `.env.example` to `.env` and configure:

```env
HOST=0.0.0.0
PORT=8000
DEBUG=true
SESSIONS_DIR=./sessions
```

## 📖 API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
