# 🚀 TeleManager - Ultra Advanced Edition

A full-stack Telegram Account Manager with **device fingerprinting**, **app spoofing**, and **proxy rotation**.

---

## ✨ Features

### 🔐 Device Fingerprinting
- **100+ Real Android Devices** - Samsung Galaxy, Google Pixel, OnePlus, Xiaomi, OPPO, Vivo, Realme, etc.
- **30+ Real iOS Devices** - iPhone 15/14/13/12/11, iPad Pro, iPad Air
- **Real System Versions** - Android 10-14, iOS 15-17
- **Unique Device Hash** - Each login gets a unique identifier

### 📲 App Spoofing
Login appears as one of these real Telegram clients:
- Telegram Android/iOS
- **Nicegram**
- **Telegram X**
- **Plus Messenger**
- **Nekogram**
- **BGram**
- **Turbo Telegram**
- **Vidogram**
- **Graph Messenger**

### 🌐 Proxy Rotation
- **One-Time Use** - Each proxy used only once, then discarded
- **Auto Skip Dead** - Automatically skips non-working proxies
- **No Retry** - Never retries on the same proxy
- **Multi-Protocol** - HTTP, HTTPS, SOCKS4, SOCKS5, MTProto
- **Validation** - Optional proxy validation before adding
- **Bulk Import** - Import hundreds of proxies at once

---

## 🔧 Quick Start

### 1️⃣ Start the Backend

```bash
cd backend

# Quick start (auto-installs)
python run.py

# Or manual
pip install -r requirements.txt
python main.py
```

Backend runs at **http://localhost:8000**

### 2️⃣ Start the Frontend

```bash
npm run dev
```

Frontend runs at **http://localhost:5173**

---

## 📡 API Endpoints

### Authentication
```
POST /api/auth/send-code     # Send OTP (with fingerprint + proxy)
POST /api/auth/verify-code   # Verify OTP
POST /api/auth/verify-2fa    # Verify 2FA password
```

### Accounts
```
GET    /api/accounts         # List all accounts
GET    /api/accounts/{id}    # Get account details
DELETE /api/accounts/{id}    # Remove account
```

### Proxies
```
GET    /api/proxies          # List proxies & stats
POST   /api/proxies          # Import proxies (bulk)
DELETE /api/proxies/used     # Remove used proxies
DELETE /api/proxies/dead     # Remove dead proxies
DELETE /api/proxies/all      # Clear all proxies
```

### Fingerprint
```
GET /api/fingerprint/preview  # Preview random fingerprint
GET /api/fingerprint/devices  # List available devices
GET /api/fingerprint/apps     # List available apps
```

---

## 📦 Proxy Import Formats

```
# Basic
host:port

# With auth
host:port:username:password

# With protocol
socks5://host:port
socks5://user:pass@host:port
http://host:port
https://user:pass@host:port
socks4://host:port
mtproto://host:port
```

---

## 🔒 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                        LOGIN FLOW                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. User enters phone + API credentials                      │
│                     ↓                                        │
│  2. Backend generates RANDOM fingerprint:                    │
│     • Device: Samsung SM-S918B (Galaxy S23 Ultra)           │
│     • App: Nicegram 10.2.1 (3847)                           │
│     • System: SDK 34 (Android 14)                           │
│     • Language: en-US                                        │
│                     ↓                                        │
│  3. Backend assigns ONE-TIME proxy:                          │
│     • socks5://45.67.89.12:1080                             │
│     • Validated: ✅ 127ms latency                           │
│                     ↓                                        │
│  4. Telethon connects to Telegram:                          │
│     • Uses fingerprint device info                          │
│     • Routes through proxy                                   │
│     • Appears as real mobile device                          │
│                     ↓                                        │
│  5. OTP sent to Telegram app                                │
│                     ↓                                        │
│  6. User verifies OTP → Account saved                       │
│                     ↓                                        │
│  7. Proxy marked as USED (never reused)                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
telemanager/
├── src/                          # React Frontend
│   ├── components/
│   │   ├── Dashboard.tsx        # Account list + stats
│   │   ├── LoginForm.tsx        # Multi-step login
│   │   └── ProxyManager.tsx     # Proxy management UI
│   ├── api.ts                   # API client
│   └── App.tsx                  # Main app
│
├── backend/                      # Python Backend
│   ├── main.py                  # FastAPI server
│   ├── telegram_manager.py      # Telethon + fingerprint
│   ├── fingerprint.py           # Device generator (100+ devices)
│   ├── proxy_manager.py         # Proxy rotation
│   ├── database.py              # SQLite storage
│   └── config.py                # Configuration
│
└── docker-compose.yml           # Docker setup
```

---

## 🎯 Device Fingerprint Example

When you login, the backend generates something like:

```json
{
  "device_model": "Samsung SM-S918B",
  "system_version": "SDK 34",
  "app_version": "10.2.5 (3891)",
  "app_name": "Nicegram",
  "lang_code": "en",
  "system_lang_code": "en-US",
  "device_hash": "a7f3c2e1b9d8"
}
```

This makes the login appear as a real Samsung Galaxy S23 Ultra running Nicegram app!

---

## ⚠️ Security Notes

1. **Session files** (`backend/sessions/`) contain login credentials - keep private!
2. **Proxies** are one-time use for security
3. **API Hash** should never be shared publicly
4. Use environment variables in production

---

## 🔮 Coming Next

Tell me to add more features:
- 📨 Send messages
- 👥 Get contacts/chats  
- 📁 Download media
- 👤 Scrape user info
- 📊 Analytics dashboard
- 🤖 Automation scripts

---

Made with 💕 - Ultra Advanced Edition!
