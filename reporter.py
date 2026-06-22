"""
Ultra-Advanced Telegram Reporting Engine v3
FULLY INTEGRATED with all systems:
- Anti-Detection Engine (risk scoring, session control)
- Network Simulator (realistic latency)
- Humanizer v2 (personality, mood, message variation)
- Account Pool (smart rotation, health, cooldowns)
- Evidence Collector (auto-collect before reporting)
- Analytics (feed every result for learning)
- Stealth Config (normal/stealth/paranoid)
"""

import asyncio
import random
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from telethon import TelegramClient
from telethon.tl.functions.account import ReportPeerRequest
from telethon.tl.functions.messages import ReportSpamRequest
from telethon.tl.functions.channels import ReportSpamRequest as ChannelReportSpamRequest
from telethon.tl.types import (
    InputReportReasonSpam,
    InputReportReasonViolence,
    InputReportReasonPornography,
    InputReportReasonChildAbuse,
    InputReportReasonCopyright,
    InputReportReasonGeoIrrelevant,
    InputReportReasonFake,
    InputReportReasonIllegalDrugs,
    InputReportReasonPersonalDetails,
    InputReportReasonOther,
)
from telethon.errors import (
    FloodWaitError,
    ChannelPrivateError,
    PeerIdInvalidError,
    UsernameNotOccupiedError,
    UsernameInvalidError,
    AuthKeyUnregisteredError,
)

import database as db
from humanizer import humanizer
from anti_detection import anti_detection
from stealth_config import StealthLevel
from account_pool import account_pool
from analytics import analytics_manager
from evidence_collector import evidence_collector


class ReportReason(Enum):
    SPAM = "spam"
    VIOLENCE = "violence"
    PORNOGRAPHY = "pornography"
    CHILD_ABUSE = "child_abuse"
    COPYRIGHT = "copyright"
    GEO_IRRELEVANT = "geo_irrelevant"
    FAKE = "fake"
    ILLEGAL_DRUGS = "illegal_drugs"
    PERSONAL_DETAILS = "personal_details"
    SCAM = "scam"
    OTHER = "other"


class TargetType(Enum):
    USER = "user"
    CHANNEL = "channel"
    GROUP = "group"
    BOT = "bot"


@dataclass
class ReportTarget:
    identifier: str
    target_type: TargetType = TargetType.USER
    resolved_id: Optional[int] = None
    resolved_name: Optional[str] = None
    access_hash: Optional[int] = None


@dataclass
class ReportSession:
    id: str
    targets: List[ReportTarget]
    reason: ReportReason
    message: str
    accounts_to_use: List[str]
    delay_min: float = 3.0
    delay_max: float = 8.0
    humanize: bool = True
    stealth_level: str = "stealth"
    collect_evidence: bool = False
    use_smart_pool: bool = True
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    total_reports: int = 0
    successful_reports: int = 0
    failed_reports: int = 0
    skipped_reports: int = 0
    results: List[Dict[str, Any]] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
    anti_detection_stats: Optional[Dict] = None


def get_report_reason_object(reason: ReportReason):
    reason_map = {
        ReportReason.SPAM: InputReportReasonSpam(),
        ReportReason.VIOLENCE: InputReportReasonViolence(),
        ReportReason.PORNOGRAPHY: InputReportReasonPornography(),
        ReportReason.CHILD_ABUSE: InputReportReasonChildAbuse(),
        ReportReason.COPYRIGHT: InputReportReasonCopyright(),
        ReportReason.GEO_IRRELEVANT: InputReportReasonGeoIrrelevant(),
        ReportReason.FAKE: InputReportReasonFake(),
        ReportReason.ILLEGAL_DRUGS: InputReportReasonIllegalDrugs(),
        ReportReason.PERSONAL_DETAILS: InputReportReasonPersonalDetails(),
        ReportReason.SCAM: InputReportReasonSpam(),
        ReportReason.OTHER: InputReportReasonOther(),
    }
    return reason_map.get(reason, InputReportReasonSpam())


class ReportManager:
    """
    v3 Report Engine - FULLY INTEGRATED
    
    Every report goes through:
    1. Account Pool → Smart account selection (health, cooldown, tier)
    2. Anti-Detection → Risk assessment (9 factors)
    3. Evidence Collector → Optional pre-report evidence gathering
    4. Humanizer v2 → Personality-based message & timing
    5. Network Simulator → Realistic latency
    6. Telethon → Actual Telegram API report
    7. Analytics → Result recorded for learning
    8. Account Pool → Post-report cooldown & health update
    """
    
    def __init__(self):
        self._active_sessions: Dict[str, ReportSession] = {}
        self._report_history: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
    
    async def resolve_target(self, client: TelegramClient, identifier: str) -> Optional[ReportTarget]:
        identifier = identifier.strip()
        if identifier.startswith("@"):
            identifier = identifier[1:]
        if "t.me/" in identifier:
            identifier = identifier.split("t.me/")[-1].split("/")[0].split("?")[0]
        
        try:
            await asyncio.sleep(random.uniform(0.3, 0.8))
            entity = await client.get_entity(identifier)
            
            target_type = TargetType.USER
            if hasattr(entity, 'megagroup') and entity.megagroup:
                target_type = TargetType.GROUP
            elif hasattr(entity, 'broadcast') and entity.broadcast:
                target_type = TargetType.CHANNEL
            elif hasattr(entity, 'bot') and entity.bot:
                target_type = TargetType.BOT
            
            return ReportTarget(
                identifier=identifier,
                target_type=target_type,
                resolved_id=entity.id,
                resolved_name=getattr(entity, 'title', None) or
                    f"{getattr(entity, 'first_name', '')} {getattr(entity, 'last_name', '')}".strip(),
                access_hash=getattr(entity, 'access_hash', None),
            )
        except (UsernameNotOccupiedError, UsernameInvalidError):
            return None
        except Exception as e:
            print(f"⚠️ Resolve error {identifier}: {e}")
            return None
    
    async def report_single(
        self,
        client: TelegramClient,
        target: ReportTarget,
        reason: ReportReason,
        message: str = "",
        humanize: bool = True,
    ) -> Dict[str, Any]:
        """Execute a single report with humanization."""
        try:
            entity = await client.get_entity(target.resolved_id or target.identifier)
            reason_obj = get_report_reason_object(reason)
            
            # Generate human-like message
            if humanize:
                final_message = humanizer.get_message_for_reason(reason.value, message)
            else:
                final_message = message or f"Reporting for {reason.value}"
            
            if len(final_message) > 4000:
                final_message = final_message[:3997] + "..."
            
            # "Thinking" delay
            if humanize:
                await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Send report
            start_time = time.time()
            await client(ReportPeerRequest(
                peer=entity,
                reason=reason_obj,
                message=final_message
            ))
            response_time = time.time() - start_time
            
            return {
                "success": True,
                "target": target.identifier,
                "target_name": target.resolved_name,
                "target_type": target.target_type.value,
                "reason": reason.value,
                "message_length": len(final_message),
                "message_preview": final_message[:80] + "..." if len(final_message) > 80 else final_message,
                "response_time": round(response_time, 3),
            }
            
        except FloodWaitError as e:
            return {"success": False, "error": f"Rate limited: {e.seconds}s", "flood_wait": e.seconds, "target": target.identifier}
        except PeerIdInvalidError:
            return {"success": False, "error": "Target not found", "target": target.identifier}
        except ChannelPrivateError:
            return {"success": False, "error": "Private channel", "target": target.identifier}
        except AuthKeyUnregisteredError:
            return {"success": False, "error": "Session expired", "target": target.identifier, "account_dead": True}
        except Exception as e:
            return {"success": False, "error": str(e), "target": target.identifier}
    
    async def execute_mass_report(
        self,
        session: ReportSession,
        get_client_func,
    ) -> ReportSession:
        """
        v3 Mass Report Engine - FULL INTEGRATION
        
        Pipeline per action:
        ┌─────────────────────────────────────────────────────┐
        │ 1. Session safety check (duration, failures)        │
        │ 2. Break/skip decision (humanizer + anti-detection) │
        │ 3. Smart account selection (pool manager)           │
        │ 4. Risk assessment (anti-detection 9 factors)       │
        │ 5. Pre-action browsing simulation                   │
        │ 6. Think delay (personality-based)                  │
        │ 7. Report execution (humanized message)             │
        │ 8. Analytics recording (feed learning engine)       │
        │ 9. Account pool update (health, cooldown)           │
        │ 10. Anti-detection action recording                 │
        │ 11. Smart delay (risk + mood + network adjusted)    │
        └─────────────────────────────────────────────────────┘
        """
        async with self._lock:
            session.status = "in_progress"
            session.started_at = time.time()
            self._active_sessions[session.id] = session
        
        # Initialize all systems
        humanizer.reset()
        
        stealth_map = {"normal": StealthLevel.NORMAL, "stealth": StealthLevel.STEALTH, "paranoid": StealthLevel.PARANOID}
        stealth_level = stealth_map.get(session.stealth_level, StealthLevel.STEALTH)
        ctx = anti_detection.create_session(session.id, stealth_level)
        
        # Sync account pool
        await account_pool.sync_from_database()
        
        print(f"\n{'='*60}")
        print(f"🚀 REPORT SESSION v3 STARTED")
        print(f"   ID: {session.id}")
        print(f"   Targets: {len(session.targets)}")
        print(f"   Accounts: {len(session.accounts_to_use)}")
        print(f"   Stealth: {stealth_level.value}")
        print(f"   Humanizer: {humanizer.get_profile_info()['personality']}")
        print(f"   Evidence: {'ON' if session.collect_evidence else 'OFF'}")
        print(f"   Smart Pool: {'ON' if session.use_smart_pool else 'OFF'}")
        print(f"{'='*60}\n")
        
        try:
            # Shuffle targets
            targets = humanizer.shuffle_with_bias(session.targets) if session.humanize else list(session.targets)
            
            # ===== PHASE 0: Evidence Collection (optional) =====
            if session.collect_evidence:
                print("📸 Phase 0: Collecting evidence before reporting...")
                for target in targets:
                    try:
                        # Use first available account for evidence
                        ev_client = await get_client_func(session.accounts_to_use[0])
                        if ev_client:
                            pkg = await evidence_collector.collect_evidence(
                                ev_client, target.identifier, session.accounts_to_use[0],
                                collect_messages=True, collect_photos=True, max_messages=30,
                            )
                            session.evidence_ids.append(pkg.id)
                            await asyncio.sleep(random.uniform(1, 3))
                    except Exception as e:
                        print(f"   ⚠️ Evidence collection failed for {target.identifier}: {e}")
                print(f"   📦 {len(session.evidence_ids)} evidence packages collected\n")
            
            # ===== PHASE 1: Reporting =====
            print("🚩 Phase 1: Executing reports...\n")
            
            for target in targets:
                # Shuffle accounts per target
                accounts = humanizer.shuffle_with_bias(session.accounts_to_use) if session.humanize else list(session.accounts_to_use)
                
                for account_id in accounts:
                    # --- CHECK 1: Should session end? ---
                    should_end, end_reason = anti_detection.should_end_session(ctx)
                    if should_end:
                        print(f"\n🛡️ Session ending: {end_reason}")
                        break
                    
                    # --- CHECK 2: Break? ---
                    break_time = await anti_detection.maybe_take_break(ctx)
                    if break_time > 0:
                        session.results.append({"event": "break", "duration": round(break_time, 1), "timestamp": datetime.utcnow().isoformat()})
                    
                    # --- CHECK 3: Natural skip? ---
                    if anti_detection.should_skip_action(ctx):
                        session.skipped_reports += 1
                        session.results.append({"target": target.identifier, "account": account_id, "skipped": True, "reason": "natural_skip", "timestamp": datetime.utcnow().isoformat()})
                        print(f"   ⏭️ Skipped (natural behavior)")
                        continue
                    
                    # --- CHECK 4: Smart account selection ---
                    if session.use_smart_pool:
                        best = await account_pool.select_best_account(target.identifier, exclude=[])
                        if best and best.account_id in session.accounts_to_use:
                            account_id = best.account_id
                        else:
                            selected = anti_detection.select_best_account(ctx, accounts, target.identifier)
                            if selected:
                                account_id = selected
                    
                    # --- CHECK 5: Risk assessment ---
                    risk_score, risk_level, risk_factors = anti_detection.assess_risk(ctx, account_id, target.identifier)
                    
                    if risk_level.value == "critical":
                        print(f"   🚨 CRITICAL RISK ({risk_score}): {', '.join(risk_factors[:2])}")
                        session.skipped_reports += 1
                        session.results.append({
                            "target": target.identifier, "account": account_id, "skipped": True,
                            "reason": f"critical_risk_{risk_score}", "risk_factors": risk_factors,
                            "timestamp": datetime.utcnow().isoformat(),
                        })
                        continue
                    elif risk_level.value == "high":
                        print(f"   ⚠️ HIGH RISK ({risk_score})")
                    
                    # --- GET CLIENT ---
                    client = await get_client_func(account_id)
                    if not client:
                        session.failed_reports += 1
                        session.results.append({"target": target.identifier, "account": account_id, "success": False, "error": "Account unavailable", "timestamp": datetime.utcnow().isoformat()})
                        # Mark in pool
                        await account_pool.record_usage(account_id, target.identifier, False, error="unavailable")
                        continue
                    
                    # Mark account as working
                    await account_pool.mark_working(account_id)
                    
                    # --- RESOLVE TARGET ---
                    if not target.resolved_id:
                        resolved = await self.resolve_target(client, target.identifier)
                        if resolved:
                            target.resolved_id = resolved.resolved_id
                            target.resolved_name = resolved.resolved_name
                            target.target_type = resolved.target_type
                            target.access_hash = resolved.access_hash
                        else:
                            session.failed_reports += 1
                            session.results.append({"target": target.identifier, "account": account_id, "success": False, "error": "Target not found", "timestamp": datetime.utcnow().isoformat()})
                            await account_pool.mark_available(account_id)
                            continue
                    
                    # --- PRE-ACTION: Browse target (stealth behavior) ---
                    if session.humanize:
                        pre_time = await anti_detection.simulate_pre_action_behavior(ctx, target.identifier)
                    
                    # --- THINK DELAY ---
                    await anti_detection.wait_think_delay(ctx)
                    
                    # --- EXECUTE REPORT ---
                    print(f"🚩 [{session.successful_reports+session.failed_reports+1}] {target.identifier} ({target.resolved_name}) | Acc: {account_id[:8]} | Risk: {risk_score} | {risk_level.value}")
                    
                    report_start = time.time()
                    result = await self.report_single(client, target, session.reason, session.message, session.humanize)
                    response_time = time.time() - report_start
                    
                    result["account"] = account_id
                    result["risk_score"] = risk_score
                    result["risk_level"] = risk_level.value
                    result["stealth_level"] = stealth_level.value
                    result["timestamp"] = datetime.utcnow().isoformat()
                    session.results.append(result)
                    session.total_reports += 1
                    
                    success = result.get("success", False)
                    flood_wait = result.get("flood_wait", 0)
                    
                    if success:
                        session.successful_reports += 1
                        print(f"   ✅ Success! ({result.get('message_length', 0)} chars, {response_time:.1f}s)")
                    else:
                        session.failed_reports += 1
                        print(f"   ❌ Failed: {result.get('error', 'Unknown')}")
                        
                        # Handle dead account
                        if result.get("account_dead"):
                            await account_pool.mark_banned(account_id)
                            continue
                        
                        # Handle flood wait
                        if flood_wait:
                            if ctx.stealth_profile.abort_on_flood_wait:
                                print(f"   🛡️ Flood wait → aborting (paranoid)")
                                ctx.should_abort = True
                                await account_pool.record_usage(account_id, target.identifier, False, flood_wait=flood_wait)
                                await account_pool.mark_available(account_id)
                                break
                            wait = min(flood_wait, 120)
                            print(f"   ⏳ Flood wait: {wait}s")
                            await asyncio.sleep(wait)
                    
                    # --- ANALYTICS: Record result ---
                    analytics_manager.record_report(
                        account_id=account_id,
                        phone="",
                        target=target.identifier,
                        reason=session.reason.value,
                        success=success,
                        error=result.get("error"),
                        flood_wait=flood_wait,
                        response_time=response_time,
                    )
                    
                    # --- ACCOUNT POOL: Update health & cooldown ---
                    await account_pool.record_usage(
                        account_id=account_id,
                        target=target.identifier,
                        success=success,
                        flood_wait=flood_wait,
                        error=result.get("error"),
                    )
                    await account_pool.mark_available(account_id)
                    
                    # --- ANTI-DETECTION: Record & delay ---
                    anti_detection.record_action(ctx, "report", account_id, target.identifier, success, response_time)
                    anti_detection.record_account_usage(ctx, account_id, cooldown_seconds=45.0)
                    
                    delay = await anti_detection.wait_action_delay(ctx, risk_score)
                    print(f"   ⏱️ Delay: {delay:.1f}s | Actions: {ctx.action_count} | Session: {ctx.session_duration_minutes:.1f}min | Health: {risk_level.value}")
                
                # Check abort after each target
                if ctx.should_abort:
                    break
            
            if session.status != "completed":
                session.status = "completed"
            
            # Get final stats
            session.anti_detection_stats = anti_detection.get_session_stats(session.id)
            
            print(f"\n{'='*60}")
            print(f"🎉 SESSION COMPLETE")
            print(f"   ✅ {session.successful_reports} | ❌ {session.failed_reports} | ⏭️ {session.skipped_reports}")
            print(f"   🛡️ Stealth: {stealth_level.value}")
            print(f"   🧠 Personality: {humanizer.get_profile_info()['personality']}")
            print(f"   ⏱️ Duration: {ctx.session_duration:.0f}s | Avg delay: {ctx.avg_delay:.1f}s")
            print(f"   📸 Evidence: {len(session.evidence_ids)} packages")
            print(f"{'='*60}\n")
            
        except Exception as e:
            session.status = "failed"
            session.results.append({"error": f"Session error: {str(e)}", "timestamp": datetime.utcnow().isoformat()})
            print(f"❌ Session failed: {e}")
        
        finally:
            session.completed_at = time.time()
            duration = session.completed_at - session.started_at if session.started_at else 0
            
            self._report_history.append({
                "session_id": session.id,
                "targets_count": len(session.targets),
                "accounts_count": len(session.accounts_to_use),
                "reason": session.reason.value,
                "stealth_level": stealth_level.value,
                "successful": session.successful_reports,
                "failed": session.failed_reports,
                "skipped": session.skipped_reports,
                "duration": duration,
                "avg_time_per_report": duration / max(session.total_reports, 1),
                "avg_delay": ctx.avg_delay,
                "evidence_count": len(session.evidence_ids),
                "anti_detection_stats": session.anti_detection_stats,
                "humanizer_profile": humanizer.get_profile_info(),
                "completed_at": datetime.utcnow().isoformat(),
            })
            
            anti_detection.end_session(session.id)
            await db.save_report_session(session)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[ReportSession]:
        return self._active_sessions.get(session_id)
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        return [{
            "id": s.id, "targets_count": len(s.targets), "status": s.status,
            "progress": f"{s.successful_reports + s.failed_reports}/{len(s.targets) * len(s.accounts_to_use)}",
            "successful": s.successful_reports, "failed": s.failed_reports,
            "skipped": s.skipped_reports, "stealth_level": s.stealth_level,
        } for s in self._active_sessions.values()]
    
    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._report_history[-limit:][::-1]
    
    def get_stats(self) -> Dict[str, Any]:
        total_sessions = len(self._report_history)
        total_reports = sum(h.get("successful", 0) + h.get("failed", 0) for h in self._report_history)
        successful = sum(h.get("successful", 0) for h in self._report_history)
        skipped = sum(h.get("skipped", 0) for h in self._report_history)
        return {
            "total_sessions": total_sessions,
            "total_reports": total_reports,
            "successful_reports": successful,
            "failed_reports": total_reports - successful,
            "skipped_reports": skipped,
            "success_rate": round((successful / total_reports * 100), 2) if total_reports > 0 else 0,
            "active_sessions": len([s for s in self._active_sessions.values() if s.status == "in_progress"]),
        }


# Global instance
report_manager = ReportManager()
