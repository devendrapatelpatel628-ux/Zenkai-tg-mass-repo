import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Server config
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Sessions directory
SESSIONS_DIR = Path(os.getenv("SESSIONS_DIR", "./sessions"))
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_PATH = Path("./data/accounts.db")
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
