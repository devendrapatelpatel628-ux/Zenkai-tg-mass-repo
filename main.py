"""
TeleManager Backend - Ultra Advanced Edition
FastAPI + Telethon + Device Fingerprinting + Proxy Rotation
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import database as db
from telegram_manager import telegram_manager
from proxy_manager import proxy_manager, Proxy, ProxyType
from fingerprint import fingerprint_generator, TELEGRAM_APPS, ANDROID_DEVICES, IOS_DEVICES
from config import HOST, PORT, DEBUG


# ==================== Pydantic Models ====================

class SendCodeRequest(BaseModel):
    phone: str = Field(..., description="Phone number with country code")
    api_id: str = Field(..., description="Telegram API ID")
    api_hash: str = Field(..., description="Telegram API Hash")
    use_proxy: bool = Field(default=True, description="Use proxy for login")


class VerifyCodeRequest(BaseModel):
    phone: str
    code: str = Field(..., min_length=5, max_length=6)


class Verify2FARequest(BaseModel):
    phone: str
    password: str


class AddProxiesRequest(BaseModel):
    proxies: List[str] = Field(..., description="List of proxy strings")
    validate: bool = Field(default=True, description="Validate proxies before adding")


class ApiResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[dict] = None
    error: Optional[str] = None


# ==================== Lifespan ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("""
╔══════════════════════════════════════════════════════════════════╗
║          🚀 TeleManager Backend - Ultra Advanced Edition          ║
╠══════════════════════════════════════════════════════════════════╣
║  ✅ Device Fingerprinting (100+ real devices)                     ║
║  ✅ App Spoofing (Nicegram, Telegram X, Plus, etc.)               ║
║  ✅ Proxy Rotation (One-time use, auto-skip dead)                 ║
║  ✅ Real Android/iOS fingerprints                                 ║
║  ✅ Mass Reporting System                                         ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    await db.init_db()
    await db.init_report_tables()
    print(f"✅ Database initialized")
    print(f"📡 Server running on http://{HOST}:{PORT}")
    print(f"📖 API Docs: http://{HOST}:{PORT}/docs")
    print(f"🔧 Debug mode: {DEBUG}")
    
    # Show proxy stats
    stats = proxy_manager.get_stats()
    print(f"🌐 Proxies: {stats['available']} available, {stats['used']} used, {stats['dead']} dead")
    
    # Start scheduler
    from scheduler import scheduler
    scheduler.start()
    print(f"📅 Scheduler started")
    
    # Sync account pool
    from account_pool import account_pool
    await account_pool.sync_from_database()
    pool_stats = account_pool.get_pool_stats()
    print(f"👥 Account Pool: {pool_stats['total']} accounts ({pool_stats['available']} available)")

    
    yield
    
    # Shutdown
    print("\\n👋 Shutting down...")
    scheduler.stop()
    await telegram_manager.disconnect_all()
    print("✅ All clients disconnected")


# ==================== FastAPI App ====================

app = FastAPI(
    title="TeleManager API - Ultra Advanced",
    description="Telegram Account Management with Fingerprinting & Proxy Rotation",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Health & Info ====================

@app.get("/")
async def root():
    """Service info."""
    return {
        "status": "ok",
        "service": "TeleManager API",
        "version": "2.0.0",
        "features": [
            "Device Fingerprinting",
            "App Spoofing",
            "Proxy Rotation",
            "Multi-account Management",
        ]
    }


@app.get("/api/health")
async def health_check():
    """API health check."""
    return {"status": "healthy"}


@app.get("/api/info")
async def get_info():
    """Get available devices, apps, and stats."""
    proxy_stats = proxy_manager.get_stats()
    
    return {
        "apps": list(TELEGRAM_APPS.keys()),
        "android_devices_count": len(ANDROID_DEVICES),
        "ios_devices_count": len(IOS_DEVICES),
        "proxy_stats": proxy_stats,
    }


# ==================== Authentication ====================

@app.post("/api/auth/send-code", response_model=ApiResponse)
async def send_code(request: SendCodeRequest):
    """
    Step 1: Send verification code with fingerprinting and proxy.
    """
    phone = request.phone.strip()
    if not phone.startswith("+"):
        phone = "+" + phone
    
    result = await telegram_manager.send_code(
        phone=phone,
        api_id=request.api_id.strip(),
        api_hash=request.api_hash.strip(),
        use_proxy=request.use_proxy,
    )
    
    if not result['success']:
        return ApiResponse(success=False, error=result.get('error', 'Unknown error'))
    
    if result.get('already_authorized'):
        return ApiResponse(
            success=True,
            message="Already logged in",
            data={
                'already_authorized': True,
                'account': result['account'],
                'fingerprint': result.get('fingerprint'),
                'proxy': result.get('proxy'),
            }
        )
    
    return ApiResponse(
        success=True,
        message="Code sent successfully",
        data={
            'phone_code_hash': result['phone_code_hash'],
            'code_type': result.get('code_type', 'SMS'),
            'fingerprint': result.get('fingerprint'),
            'proxy': result.get('proxy'),
        }
    )


@app.post("/api/auth/verify-code", response_model=ApiResponse)
async def verify_code(request: VerifyCodeRequest):
    """Step 2: Verify the OTP code."""
    phone = request.phone.strip()
    if not phone.startswith("+"):
        phone = "+" + phone
    
    result = await telegram_manager.verify_code(
        phone=phone,
        code=request.code.strip()
    )
    
    if not result['success']:
        return ApiResponse(success=False, error=result.get('error', 'Unknown error'))
    
    if result.get('needs_2fa'):
        return ApiResponse(
            success=True,
            message="2FA required",
            data={'needs_2fa': True}
        )
    
    return ApiResponse(
        success=True,
        message="Login successful",
        data={
            'account': result['account'],
            'fingerprint': result.get('fingerprint'),
        }
    )


@app.post("/api/auth/verify-2fa", response_model=ApiResponse)
async def verify_2fa(request: Verify2FARequest):
    """Step 3: Verify 2FA password."""
    phone = request.phone.strip()
    if not phone.startswith("+"):
        phone = "+" + phone
    
    result = await telegram_manager.verify_2fa(
        phone=phone,
        password=request.password
    )
    
    if not result['success']:
        return ApiResponse(success=False, error=result.get('error', 'Unknown error'))
    
    return ApiResponse(
        success=True,
        message="Login successful",
        data={
            'account': result['account'],
            'fingerprint': result.get('fingerprint'),
        }
    )


# ==================== Accounts ====================

@app.get("/api/accounts")
async def get_accounts():
    """Get all saved accounts."""
    accounts = await db.get_all_accounts()
    
    formatted = []
    for acc in accounts:
        formatted.append({
            'id': acc['id'],
            'phone': acc['phone'],
            'firstName': acc['first_name'] or 'Unknown',
            'lastName': acc['last_name'] or '',
            'username': acc['username'] or '',
            'apiId': acc['api_id'],
            'apiHash': acc['api_hash'],
            'status': acc['status'] or 'offline',
            'loginDate': acc['login_date'] or acc['created_at'],
            'deviceModel': acc.get('device_model'),
            'appName': acc.get('app_name'),
        })
    
    return {'success': True, 'accounts': formatted}


@app.get("/api/accounts/{account_id}")
async def get_account(account_id: str):
    """Get a specific account."""
    account = await db.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return {
        'success': True,
        'account': {
            'id': account['id'],
            'phone': account['phone'],
            'firstName': account['first_name'] or 'Unknown',
            'lastName': account['last_name'] or '',
            'username': account['username'] or '',
            'apiId': account['api_id'],
            'apiHash': account['api_hash'],
            'status': account['status'] or 'offline',
            'loginDate': account['login_date'] or account['created_at'],
            'deviceModel': account.get('device_model'),
            'appName': account.get('app_name'),
        }
    }


@app.get("/api/accounts/{account_id}/status")
async def check_account_status(account_id: str):
    """Check account session validity."""
    result = await telegram_manager.check_account_status(account_id)
    
    if not result['success']:
        return ApiResponse(success=False, error=result.get('error'))
    
    return ApiResponse(
        success=True,
        data={
            'status': result['status'],
            'valid': result.get('valid', False),
            'user': result.get('user')
        }
    )


@app.delete("/api/accounts/{account_id}")
async def delete_account(account_id: str):
    """Logout and remove an account."""
    result = await telegram_manager.logout_account(account_id)
    
    if not result['success']:
        return ApiResponse(success=False, error=result.get('error'))
    
    return ApiResponse(success=True, message="Account removed successfully")


# ==================== Proxy Management ====================

@app.get("/api/proxies")
async def get_proxies():
    """Get all proxies and stats."""
    return {
        'success': True,
        'proxies': proxy_manager.get_all_proxies(),
        'stats': proxy_manager.get_stats(),
    }


@app.post("/api/proxies")
async def add_proxies(request: AddProxiesRequest):
    """
    Add proxies to the pool.
    
    Supported formats:
    - host:port
    - host:port:user:pass
    - socks5://host:port
    - socks5://user:pass@host:port
    - http://host:port
    """
    result = await proxy_manager.add_proxies_bulk(
        request.proxies,
        validate=request.validate
    )
    
    return {
        'success': True,
        'added': result['added'],
        'failed': result['failed'],
        'duplicates': result['duplicates'],
        'errors': result['errors'][:10],  # Limit errors shown
        'stats': proxy_manager.get_stats(),
    }


@app.delete("/api/proxies/used")
async def remove_used_proxies():
    """Remove all used proxies from pool."""
    removed = await proxy_manager.remove_used_proxies()
    return {
        'success': True,
        'removed': removed,
        'stats': proxy_manager.get_stats(),
    }


@app.delete("/api/proxies/dead")
async def remove_dead_proxies():
    """Remove all dead proxies from pool."""
    await proxy_manager.remove_dead_proxies()
    return {
        'success': True,
        'message': 'Dead proxies removed',
        'stats': proxy_manager.get_stats(),
    }


@app.delete("/api/proxies/all")
async def clear_all_proxies():
    """Clear all proxies."""
    await proxy_manager.clear_all_proxies()
    return {
        'success': True,
        'message': 'All proxies cleared',
    }


# ==================== Fingerprint Preview ====================

@app.get("/api/fingerprint/preview")
async def preview_fingerprint():
    """
    Generate and preview a random fingerprint.
    Useful for testing what device info will be used.
    """
    fp = fingerprint_generator.generate_random_fingerprint()
    return {
        'success': True,
        'fingerprint': fingerprint_generator.get_fingerprint_info(fp),
        'full_details': {
            'device_model': fp.device_model,
            'system_version': fp.system_version,
            'app_version': fp.app_version,
            'app_name': fp.app_name,
            'lang_code': fp.lang_code,
            'system_lang_code': fp.system_lang_code,
            'layer': fp.layer,
            'sdk': fp.sdk,
        }
    }


@app.get("/api/fingerprint/devices")
async def get_available_devices():
    """Get list of available device models."""
    android_brands = {}
    for d in ANDROID_DEVICES:
        brand = d['brand']
        if brand not in android_brands:
            android_brands[brand] = []
        android_brands[brand].append(d['name'])
    
    ios_models = [d['name'] for d in IOS_DEVICES]
    
    return {
        'android': android_brands,
        'ios': ios_models,
        'total_android': len(ANDROID_DEVICES),
        'total_ios': len(IOS_DEVICES),
    }


@app.get("/api/fingerprint/apps")
async def get_available_apps():
    """Get list of available Telegram apps for spoofing."""
    apps = []
    for key, app in TELEGRAM_APPS.items():
        apps.append({
            'key': key,
            'name': app['app_name'],
            'layer': app['layer'],
        })
    return {'apps': apps}


# ==================== Reporting ====================

from reporter import report_manager, ReportReason, ReportTarget, ReportSession, TargetType
import uuid


class ReportRequest(BaseModel):
    targets: List[str] = Field(..., description="List of usernames or IDs to report")
    reason: str = Field(..., description="Report reason (spam, violence, fake, etc.)")
    message: str = Field(default="", max_length=4000, description="Report description (up to 4000 chars)")
    account_ids: List[str] = Field(..., description="Account IDs to use for reporting")
    delay_min: float = Field(default=3.0, description="Minimum delay between reports")
    delay_max: float = Field(default=10.0, description="Maximum delay between reports")
    humanize: bool = Field(default=True, description="Enable human-like behavior")
    stealth_level: str = Field(default="stealth", description="Stealth level: normal, stealth, paranoid")
    collect_evidence: bool = Field(default=False, description="Collect evidence before reporting")
    use_smart_pool: bool = Field(default=True, description="Use smart account pool for selection")


class ResolveTargetRequest(BaseModel):
    target: str = Field(..., description="Username or ID to resolve")
    account_id: str = Field(..., description="Account ID to use for resolving")


@app.get("/api/reports/reasons")
async def get_report_reasons():
    """Get available report reasons."""
    reasons = [
        {"id": "spam", "name": "Spam", "description": "Unwanted promotional content"},
        {"id": "scam", "name": "Scam/Fraud", "description": "Fraudulent schemes or scams"},
        {"id": "fake", "name": "Fake Account", "description": "Impersonation or fake identity"},
        {"id": "violence", "name": "Violence", "description": "Violent or dangerous content"},
        {"id": "pornography", "name": "Pornography", "description": "Adult/NSFW content"},
        {"id": "child_abuse", "name": "Child Abuse", "description": "Content exploiting minors"},
        {"id": "illegal_drugs", "name": "Illegal Drugs", "description": "Drug-related content"},
        {"id": "copyright", "name": "Copyright", "description": "Copyright infringement"},
        {"id": "personal_details", "name": "Personal Details", "description": "Sharing private information"},
        {"id": "other", "name": "Other", "description": "Other violations"},
    ]
    return {"reasons": reasons}


@app.post("/api/reports/resolve")
async def resolve_target(request: ResolveTargetRequest):
    """Resolve a username/ID to get target info."""
    account = await db.get_account(request.account_id)
    if not account:
        return ApiResponse(success=False, error="Account not found")
    
    client = await telegram_manager.get_client(account['phone'])
    if not client:
        return ApiResponse(success=False, error="Account not connected")
    
    target = await report_manager.resolve_target(client, request.target)
    
    if not target:
        return ApiResponse(success=False, error="Could not resolve target")
    
    return ApiResponse(
        success=True,
        data={
            "identifier": target.identifier,
            "type": target.target_type.value,
            "id": target.resolved_id,
            "name": target.resolved_name,
        }
    )


@app.post("/api/reports/start")
async def start_report_session(request: ReportRequest):
    """Start a new reporting session."""
    # Validate reason
    try:
        reason = ReportReason(request.reason)
    except ValueError:
        return ApiResponse(success=False, error=f"Invalid reason: {request.reason}")
    
    # Validate accounts
    valid_accounts = []
    for acc_id in request.account_ids:
        account = await db.get_account(acc_id)
        if account:
            valid_accounts.append(acc_id)
    
    if not valid_accounts:
        return ApiResponse(success=False, error="No valid accounts provided")
    
    # Create targets
    targets = [ReportTarget(identifier=t) for t in request.targets]
    
    # Validate stealth level
    valid_levels = ["normal", "stealth", "paranoid"]
    stealth = request.stealth_level if request.stealth_level in valid_levels else "stealth"
    
    # Create session with FULL integration
    session = ReportSession(
        id=str(uuid.uuid4())[:8],
        targets=targets,
        reason=reason,
        message=request.message,
        accounts_to_use=valid_accounts,
        delay_min=request.delay_min,
        delay_max=request.delay_max,
        humanize=request.humanize,
        stealth_level=stealth,
        collect_evidence=request.collect_evidence,
        use_smart_pool=request.use_smart_pool,
    )
    
    # Define function to get client
    async def get_client_by_id(account_id: str):
        account = await db.get_account(account_id)
        if account:
            return await telegram_manager.get_client(account['phone'])
        return None
    
    # Start reporting in background
    asyncio.create_task(
        report_manager.execute_mass_report(session, get_client_by_id)
    )
    
    return ApiResponse(
        success=True,
        message="Report session started",
        data={
            "session_id": session.id,
            "targets_count": len(targets),
            "accounts_count": len(valid_accounts),
            "reason": reason.value,
        }
    )


@app.get("/api/reports/sessions")
async def get_report_sessions():
    """Get all report sessions."""
    sessions = await db.get_report_sessions(limit=50)
    active = report_manager.get_active_sessions()
    
    return {
        "success": True,
        "sessions": sessions,
        "active": active,
    }


@app.get("/api/reports/sessions/{session_id}")
async def get_report_session(session_id: str):
    """Get a specific report session."""
    session = report_manager.get_session(session_id)
    
    if session:
        return {
            "success": True,
            "session": {
                "id": session.id,
                "status": session.status,
                "targets": [t.identifier for t in session.targets],
                "reason": session.reason.value,
                "total_reports": session.total_reports,
                "successful": session.successful_reports,
                "failed": session.failed_reports,
                "results": session.results[-20:],  # Last 20 results
            }
        }
    
    # Try to get from database
    sessions = await db.get_report_sessions(limit=100)
    for s in sessions:
        if s['id'] == session_id:
            return {"success": True, "session": s}
    
    return ApiResponse(success=False, error="Session not found")


@app.get("/api/reports/stats")
async def get_report_stats():
    """Get reporting statistics."""
    db_stats = await db.get_report_stats()
    manager_stats = report_manager.get_stats()
    
    return {
        "success": True,
        "stats": {
            **db_stats,
            "active_sessions": manager_stats.get("active_sessions", 0),
        }
    }


@app.get("/api/reports/history")
async def get_report_history():
    """Get report history."""
    history = report_manager.get_history(limit=100)
    return {"success": True, "history": history}


# ==================== Analytics ====================

from analytics import analytics_manager


@app.get("/api/analytics/dashboard")
async def get_analytics_dashboard():
    """Get complete analytics dashboard."""
    return {
        "success": True,
        **analytics_manager.get_full_dashboard()
    }


@app.get("/api/analytics/insights")
async def get_analytics_insights():
    """Get AI-like insights and recommendations."""
    return {
        "success": True,
        **analytics_manager.get_insights()
    }


@app.get("/api/analytics/best-hours")
async def get_best_hours():
    """Get best hours for reporting."""
    return {
        "success": True,
        "best_hours": analytics_manager.get_best_hours(5),
        "worst_hours": analytics_manager.get_worst_hours(3),
    }


@app.get("/api/analytics/accounts")
async def get_account_analytics():
    """Get account performance rankings."""
    return {
        "success": True,
        "rankings": analytics_manager.get_account_rankings(),
        "needing_rest": analytics_manager.get_accounts_needing_rest(),
        "best_performers": analytics_manager.get_best_accounts(),
    }


# ==================== Warmup ====================

from warmup import warmup_manager


@app.get("/api/warmup/profiles")
async def get_warmup_profiles():
    """Get all warmup profiles."""
    return {
        "success": True,
        "profiles": warmup_manager.get_all_profiles(),
        "stats": warmup_manager.get_stats(),
    }


@app.get("/api/warmup/accounts/{account_id}")
async def get_account_warmup(account_id: str):
    """Get warmup status for an account."""
    readiness = warmup_manager.get_account_readiness(account_id)
    profile = warmup_manager.get_profile(account_id)
    
    return {
        "success": True,
        "readiness": readiness,
        "profile": profile.to_dict() if profile else None,
    }


class WarmupRequest(BaseModel):
    account_id: str
    actions: int = Field(default=5, ge=1, le=20)


@app.post("/api/warmup/run")
async def run_warmup(request: WarmupRequest):
    """Run a warmup session for an account."""
    account = await db.get_account(request.account_id)
    if not account:
        return ApiResponse(success=False, error="Account not found")
    
    client = await telegram_manager.get_client(account['phone'])
    if not client:
        return ApiResponse(success=False, error="Account not connected")
    
    profile = warmup_manager.get_or_create_profile(request.account_id, account['phone'])
    
    result = await warmup_manager.run_warmup_session(client, profile, request.actions)
    
    return {
        "success": True,
        **result
    }


# ==================== Scheduler & Campaigns ====================

from scheduler import scheduler, TaskType
from datetime import datetime


class ScheduleReportRequest(BaseModel):
    targets: List[str]
    reason: str
    account_ids: List[str]
    scheduled_time: str = ""  # ISO format, empty = auto-optimize
    message: str = ""
    humanize: bool = True
    stealth_level: str = "stealth"


class CreateCampaignRequest(BaseModel):
    name: str = Field(..., description="Campaign name")
    targets: List[str] = Field(..., description="Target usernames")
    reason: str = Field(default="spam")
    account_ids: List[str] = Field(..., description="Account IDs to use")
    message: str = ""
    stealth_level: str = "stealth"
    total_waves: int = Field(default=3, ge=1, le=20)
    hours_between_waves: float = Field(default=6.0, ge=0.5, le=48)
    accounts_per_wave: int = Field(default=0, ge=0)
    distribution: str = Field(default="natural", description="uniform, natural, burst, spread, random")


@app.post("/api/scheduler/report")
async def schedule_report(request: ScheduleReportRequest):
    """Schedule a report. Leave scheduled_time empty for auto-optimal scheduling."""
    if request.scheduled_time:
        try:
            scheduled_time = datetime.fromisoformat(request.scheduled_time.replace("Z", "+00:00"))
        except:
            return ApiResponse(success=False, error="Invalid datetime format")
        
        if scheduled_time < datetime.now():
            return ApiResponse(success=False, error="Cannot schedule in the past")
        
        task = scheduler.schedule_task(
            task_type=TaskType.REPORT,
            scheduled_time=scheduled_time,
            data={
                "targets": request.targets, "reason": request.reason,
                "account_ids": request.account_ids, "message": request.message,
                "humanize": request.humanize, "stealth_level": request.stealth_level,
            },
        )
    else:
        # Auto-schedule at optimal time
        task = scheduler.schedule_report_auto(
            targets=request.targets, reason=request.reason,
            account_ids=request.account_ids, message=request.message,
            humanize=request.humanize, stealth_level=request.stealth_level,
        )
    
    return {"success": True, "task": task.to_dict()}


@app.post("/api/scheduler/campaign")
async def create_campaign(request: CreateCampaignRequest):
    """Create a multi-wave reporting campaign."""
    campaign = scheduler.create_campaign(
        name=request.name,
        targets=request.targets,
        reason=request.reason,
        account_ids=request.account_ids,
        message=request.message,
        stealth_level=request.stealth_level,
        total_waves=request.total_waves,
        hours_between_waves=request.hours_between_waves,
        accounts_per_wave=request.accounts_per_wave,
        distribution=request.distribution,
    )
    
    return {"success": True, "campaign": campaign.to_dict()}


@app.get("/api/scheduler/campaigns")
async def get_campaigns():
    """Get all campaigns."""
    return {
        "success": True,
        "campaigns": scheduler.get_campaigns(),
    }


@app.get("/api/scheduler/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str):
    """Get campaign details."""
    data = scheduler.get_campaign(campaign_id)
    if not data:
        return ApiResponse(success=False, error="Campaign not found")
    return {"success": True, "campaign": data}


@app.post("/api/scheduler/campaigns/{campaign_id}/pause")
async def pause_campaign(campaign_id: str):
    """Pause a campaign."""
    if scheduler.pause_campaign(campaign_id):
        return {"success": True, "message": "Campaign paused"}
    return ApiResponse(success=False, error="Campaign not found")


@app.post("/api/scheduler/campaigns/{campaign_id}/resume")
async def resume_campaign(campaign_id: str):
    """Resume a paused campaign."""
    if scheduler.resume_campaign(campaign_id):
        return {"success": True, "message": "Campaign resumed"}
    return ApiResponse(success=False, error="Campaign not found")


@app.delete("/api/scheduler/campaigns/{campaign_id}")
async def cancel_campaign(campaign_id: str):
    """Cancel a campaign."""
    if scheduler.cancel_campaign(campaign_id):
        return {"success": True, "message": "Campaign cancelled"}
    return ApiResponse(success=False, error="Campaign not found")


@app.get("/api/scheduler/tasks")
async def get_scheduled_tasks():
    """Get all scheduled tasks."""
    return {
        "success": True,
        "tasks": scheduler.get_pending_tasks(),
        "all_tasks": scheduler.get_all_tasks(limit=20),
        "stats": scheduler.get_stats(),
        "next_task": scheduler.get_next_task(),
    }


@app.delete("/api/scheduler/tasks/{task_id}")
async def cancel_scheduled_task(task_id: str):
    """Cancel a scheduled task."""
    if scheduler.cancel_task(task_id):
        return {"success": True, "message": "Task cancelled"}
    return ApiResponse(success=False, error="Task not found or already executed")


@app.get("/api/scheduler/optimal-hours")
async def get_optimal_hours():
    """Get scored hours for scheduling insights."""
    return {
        "success": True,
        "hours": scheduler.get_optimal_hours(),
    }


# ==================== Account Pool ====================

from account_pool import account_pool


@app.get("/api/pool")
async def get_pool():
    """Get full account pool status."""
    await account_pool.sync_from_database()
    return {
        "success": True,
        "accounts": account_pool.get_all_accounts(),
        "stats": account_pool.get_pool_stats(),
        "recommendations": account_pool.get_recommendations(),
    }


@app.get("/api/pool/stats")
async def get_pool_stats():
    """Get pool statistics."""
    return {
        "success": True,
        "stats": account_pool.get_pool_stats(),
    }


@app.get("/api/pool/accounts/{account_id}")
async def get_pool_account(account_id: str):
    """Get single account pool details."""
    data = account_pool.get_account(account_id)
    if not data:
        return ApiResponse(success=False, error="Account not in pool")
    return {"success": True, "account": data}


class RestAccountRequest(BaseModel):
    account_id: str
    hours: float = Field(default=6.0, ge=0.5, le=72)


@app.post("/api/pool/rest")
async def rest_pool_account(request: RestAccountRequest):
    """Send an account to rest."""
    await account_pool.rest_account(request.account_id, request.hours)
    return {"success": True, "message": f"Account resting for {request.hours}h"}


@app.post("/api/pool/wake/{account_id}")
async def wake_pool_account(account_id: str):
    """Wake a resting account."""
    await account_pool.wake_account(account_id)
    return {"success": True, "message": "Account awakened"}


@app.get("/api/pool/recommendations")
async def get_pool_recommendations():
    """Get pool recommendations."""
    return {
        "success": True,
        "recommendations": account_pool.get_recommendations(),
    }


@app.post("/api/pool/select")
async def select_best_accounts(target: str = "", count: int = 3):
    """Preview which accounts would be selected for a target."""
    accounts = await account_pool.select_accounts(target or "test_target", count)
    return {
        "success": True,
        "selected": [a.to_dict() for a in accounts],
    }


# ==================== Evidence Collection ====================

from evidence_collector import evidence_collector
from fastapi.responses import FileResponse


class CollectEvidenceRequest(BaseModel):
    target: str = Field(..., description="Username or ID")
    account_id: str = Field(..., description="Account to use for collection")
    collect_messages: bool = True
    collect_photos: bool = True
    max_messages: int = Field(default=50, ge=1, le=200)


@app.post("/api/evidence/collect")
async def collect_evidence(request: CollectEvidenceRequest):
    """Collect evidence from a target."""
    account = await db.get_account(request.account_id)
    if not account:
        return ApiResponse(success=False, error="Account not found")
    
    client = await telegram_manager.get_client(account['phone'])
    if not client:
        return ApiResponse(success=False, error="Account not connected")
    
    # Run collection in background
    pkg = await evidence_collector.collect_evidence(
        client=client,
        target=request.target,
        account_id=request.account_id,
        collect_messages=request.collect_messages,
        collect_photos=request.collect_photos,
        max_messages=request.max_messages,
    )
    
    return {
        "success": True,
        "package": pkg.to_dict(),
    }


@app.get("/api/evidence")
async def get_evidence_packages():
    """Get all evidence packages."""
    return {
        "success": True,
        "packages": evidence_collector.get_all_packages(),
        "stats": evidence_collector.get_stats(),
    }


@app.get("/api/evidence/{package_id}")
async def get_evidence_package(package_id: str):
    """Get single evidence package with details."""
    data = evidence_collector.get_package(package_id)
    if not data:
        return ApiResponse(success=False, error="Package not found")
    return {"success": True, "package": data}


@app.post("/api/evidence/{package_id}/export")
async def export_evidence(package_id: str):
    """Export evidence package as downloadable ZIP."""
    zip_path = await evidence_collector.export_package(package_id)
    if not zip_path:
        return ApiResponse(success=False, error="Export failed")
    return {"success": True, "export_path": zip_path}


@app.get("/api/evidence/{package_id}/download")
async def download_evidence(package_id: str):
    """Download the exported ZIP file."""
    pkg = evidence_collector.get_package(package_id)
    if not pkg or not pkg.get("export_path"):
        # Try exporting first
        zip_path = await evidence_collector.export_package(package_id)
        if not zip_path:
            raise HTTPException(status_code=404, detail="Evidence not found or export failed")
    else:
        zip_path = pkg["export_path"]
    
    file_path = Path(zip_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/zip",
    )


@app.delete("/api/evidence/{package_id}")
async def delete_evidence(package_id: str):
    """Delete an evidence package."""
    deleted = await evidence_collector.delete_package(package_id)
    if not deleted:
        return ApiResponse(success=False, error="Package not found")
    return {"success": True, "message": "Evidence deleted"}


# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
    )
