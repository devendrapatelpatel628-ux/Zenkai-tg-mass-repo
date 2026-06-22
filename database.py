"""
Database operations for TeleManager
Stores accounts, pending logins, fingerprints, and proxy usage
"""

import aiosqlite
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from config import DATABASE_PATH


async def init_db():
    """Initialize the database with required tables."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Accounts table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                phone TEXT UNIQUE NOT NULL,
                api_id TEXT NOT NULL,
                api_hash TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                user_id INTEGER,
                session_file TEXT,
                status TEXT DEFAULT 'offline',
                login_date TEXT,
                device_model TEXT,
                app_name TEXT,
                proxy_used TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Pending logins table (with fingerprint and proxy info)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS pending_logins (
                phone TEXT PRIMARY KEY,
                api_id TEXT NOT NULL,
                api_hash TEXT NOT NULL,
                phone_code_hash TEXT,
                fingerprint_info TEXT,
                proxy_info TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Proxy usage history
        await db.execute("""
            CREATE TABLE IF NOT EXISTS proxy_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proxy_id TEXT,
                phone TEXT,
                used_at TEXT,
                success INTEGER DEFAULT 0,
                error TEXT
            )
        """)
        
        await db.commit()


async def save_pending_login(
    phone: str,
    api_id: str,
    api_hash: str,
    phone_code_hash: str,
    fingerprint_info: Optional[Dict[str, Any]] = None,
    proxy_info: Optional[Dict[str, Any]] = None,
):
    """Save a pending login attempt with fingerprint and proxy info."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO pending_logins 
            (phone, api_id, api_hash, phone_code_hash, fingerprint_info, proxy_info, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            phone,
            api_id,
            api_hash,
            phone_code_hash,
            json.dumps(fingerprint_info) if fingerprint_info else None,
            json.dumps(proxy_info) if proxy_info else None,
            datetime.utcnow().isoformat(),
        ))
        await db.commit()


async def get_pending_login(phone: str) -> Optional[dict]:
    """Get a pending login by phone."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM pending_logins WHERE phone = ?", (phone,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                data = dict(row)
                if data.get('fingerprint_info'):
                    data['fingerprint_info'] = json.loads(data['fingerprint_info'])
                if data.get('proxy_info'):
                    data['proxy_info'] = json.loads(data['proxy_info'])
                return data
            return None


async def delete_pending_login(phone: str):
    """Delete a pending login."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM pending_logins WHERE phone = ?", (phone,))
        await db.commit()


async def save_account(account: dict):
    """Save an account to the database."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO accounts 
            (id, phone, api_id, api_hash, first_name, last_name, username, user_id, 
             session_file, status, login_date, device_model, app_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            account['id'],
            account['phone'],
            account['api_id'],
            account['api_hash'],
            account.get('first_name', ''),
            account.get('last_name', ''),
            account.get('username', ''),
            account.get('user_id'),
            account.get('session_file', ''),
            account.get('status', 'offline'),
            account.get('login_date', datetime.utcnow().isoformat()),
            account.get('device_model'),
            account.get('app_name'),
        ))
        await db.commit()


async def get_all_accounts() -> List[dict]:
    """Get all accounts."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM accounts ORDER BY created_at DESC") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_account(account_id: str) -> Optional[dict]:
    """Get an account by ID."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM accounts WHERE id = ?", (account_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_account_by_phone(phone: str) -> Optional[dict]:
    """Get an account by phone number."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM accounts WHERE phone = ?", (phone,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def update_account_status(account_id: str, status: str):
    """Update account status."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE accounts SET status = ? WHERE id = ?",
            (status, account_id)
        )
        await db.commit()


async def delete_account(account_id: str) -> bool:
    """Delete an account."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM accounts WHERE id = ?", (account_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


async def log_proxy_usage(proxy_id: str, phone: str, success: bool, error: Optional[str] = None):
    """Log proxy usage for analytics."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO proxy_history (proxy_id, phone, used_at, success, error)
            VALUES (?, ?, ?, ?, ?)
        """, (proxy_id, phone, datetime.utcnow().isoformat(), 1 if success else 0, error))
        await db.commit()


async def get_proxy_stats() -> Dict[str, Any]:
    """Get proxy usage statistics."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Total usage
        async with db.execute("SELECT COUNT(*) as total FROM proxy_history") as cursor:
            row = await cursor.fetchone()
            total = row['total'] if row else 0
        
        # Success rate
        async with db.execute(
            "SELECT COUNT(*) as success FROM proxy_history WHERE success = 1"
        ) as cursor:
            row = await cursor.fetchone()
            success = row['success'] if row else 0
        
        return {
            "total_uses": total,
            "successful": success,
            "failed": total - success,
            "success_rate": round((success / total * 100), 2) if total > 0 else 0,
        }


# ==================== Report Sessions ====================

async def init_report_tables():
    """Initialize report-related tables."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS report_sessions (
                id TEXT PRIMARY KEY,
                targets TEXT,
                reason TEXT,
                message TEXT,
                accounts_used TEXT,
                status TEXT DEFAULT 'pending',
                total_reports INTEGER DEFAULT 0,
                successful_reports INTEGER DEFAULT 0,
                failed_reports INTEGER DEFAULT 0,
                results TEXT,
                created_at TEXT,
                started_at TEXT,
                completed_at TEXT
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS report_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                target TEXT,
                target_name TEXT,
                target_type TEXT,
                reason TEXT,
                account_id TEXT,
                account_phone TEXT,
                success INTEGER DEFAULT 0,
                error TEXT,
                reported_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.commit()


async def save_report_session(session) -> None:
    """Save a report session to database."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        targets_json = json.dumps([{
            'identifier': t.identifier,
            'type': t.target_type.value if hasattr(t.target_type, 'value') else t.target_type,
            'resolved_id': t.resolved_id,
            'resolved_name': t.resolved_name,
        } for t in session.targets])
        
        await db.execute("""
            INSERT OR REPLACE INTO report_sessions
            (id, targets, reason, message, accounts_used, status, total_reports,
             successful_reports, failed_reports, results, created_at, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session.id,
            targets_json,
            session.reason.value if hasattr(session.reason, 'value') else session.reason,
            session.message,
            json.dumps(session.accounts_to_use),
            session.status,
            session.total_reports,
            session.successful_reports,
            session.failed_reports,
            json.dumps(session.results),
            datetime.fromtimestamp(session.created_at).isoformat() if session.created_at else None,
            datetime.fromtimestamp(session.started_at).isoformat() if session.started_at else None,
            datetime.fromtimestamp(session.completed_at).isoformat() if session.completed_at else None,
        ))
        await db.commit()


async def get_report_sessions(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent report sessions."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM report_sessions ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            sessions = []
            for row in rows:
                data = dict(row)
                data['targets'] = json.loads(data['targets']) if data.get('targets') else []
                data['accounts_used'] = json.loads(data['accounts_used']) if data.get('accounts_used') else []
                data['results'] = json.loads(data['results']) if data.get('results') else []
                sessions.append(data)
            return sessions


async def get_report_stats() -> Dict[str, Any]:
    """Get overall reporting statistics."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Total sessions
        async with db.execute("SELECT COUNT(*) as total FROM report_sessions") as cursor:
            row = await cursor.fetchone()
            total_sessions = row['total'] if row else 0
        
        # Total reports
        async with db.execute(
            "SELECT SUM(successful_reports) as success, SUM(failed_reports) as failed FROM report_sessions"
        ) as cursor:
            row = await cursor.fetchone()
            successful = row['success'] or 0
            failed = row['failed'] or 0
        
        # Today's reports
        today = datetime.utcnow().strftime('%Y-%m-%d')
        async with db.execute(
            "SELECT SUM(successful_reports) as today FROM report_sessions WHERE created_at LIKE ?",
            (f"{today}%",)
        ) as cursor:
            row = await cursor.fetchone()
            today_reports = row['today'] or 0
        
        return {
            "total_sessions": total_sessions,
            "total_reports": successful + failed,
            "successful_reports": successful,
            "failed_reports": failed,
            "success_rate": round((successful / (successful + failed) * 100), 2) if (successful + failed) > 0 else 0,
            "today_reports": today_reports,
        }
