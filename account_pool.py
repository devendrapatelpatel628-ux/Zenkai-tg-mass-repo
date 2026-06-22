"""
Smart Account Pool Manager
Intelligent account rotation, cooling, health monitoring, and risk-based selection.
Prevents account burns and maximizes longevity.
"""

import asyncio
import random
import time
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
from collections import deque

import database as db


class AccountTier(Enum):
    """Account trust levels based on age, warmup, and history."""
    FRESH = "fresh"             # 0-3 days, barely warmed up
    ROOKIE = "rookie"           # 3-7 days, lightly used
    REGULAR = "regular"         # 7-14 days, moderate use
    VETERAN = "veteran"         # 14-30 days, well established
    ELITE = "elite"             # 30+ days, high trust


class AccountState(Enum):
    """Current account operational state."""
    AVAILABLE = "available"     # Ready to use
    COOLING = "cooling"         # On cooldown, temporarily unavailable
    RESTING = "resting"         # Needs extended rest (low health)
    WORKING = "working"         # Currently in use by a session
    BANNED = "banned"           # Detected as banned/restricted
    DEAD = "dead"               # Session expired or logout


class CooldownReason(Enum):
    """Why an account is cooling down."""
    POST_REPORT = "post_report"
    FLOOD_WAIT = "flood_wait"
    HIGH_USAGE = "high_usage"
    SCHEDULED_REST = "scheduled_rest"
    ERROR_RECOVERY = "error_recovery"
    MANUAL = "manual"


@dataclass
class AccountCooldown:
    """Active cooldown for an account."""
    reason: CooldownReason
    started_at: float
    duration: float  # seconds
    
    @property
    def remaining(self) -> float:
        elapsed = time.time() - self.started_at
        return max(0, self.duration - elapsed)
    
    @property
    def is_expired(self) -> bool:
        return self.remaining <= 0


@dataclass
class AccountHealth:
    """Comprehensive health metrics for an account."""
    score: float = 100.0            # 0-100, higher = healthier
    
    # Lifetime stats
    total_reports: int = 0
    successful_reports: int = 0
    failed_reports: int = 0
    flood_waits: int = 0
    total_flood_wait_seconds: int = 0
    errors: int = 0
    
    # Rolling window (last 24h)
    recent_reports: int = 0
    recent_failures: int = 0
    recent_flood_waits: int = 0
    
    # Streaks
    current_success_streak: int = 0
    current_failure_streak: int = 0
    best_success_streak: int = 0
    worst_failure_streak: int = 0
    
    # Timing
    last_used: Optional[float] = None
    last_success: Optional[float] = None
    last_failure: Optional[float] = None
    last_flood_wait: Optional[float] = None
    last_health_update: Optional[float] = None
    
    @property
    def success_rate(self) -> float:
        if self.total_reports == 0:
            return 100.0
        return round((self.successful_reports / self.total_reports) * 100, 2)
    
    @property
    def hours_since_last_use(self) -> float:
        if not self.last_used:
            return 999.0
        return (time.time() - self.last_used) / 3600
    
    @property
    def hours_since_last_flood(self) -> float:
        if not self.last_flood_wait:
            return 999.0
        return (time.time() - self.last_flood_wait) / 3600
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 1),
            "total_reports": self.total_reports,
            "successful": self.successful_reports,
            "failed": self.failed_reports,
            "success_rate": self.success_rate,
            "flood_waits": self.flood_waits,
            "current_streak": self.current_success_streak,
            "best_streak": self.best_success_streak,
            "hours_since_use": round(self.hours_since_last_use, 1),
            "recent_reports_24h": self.recent_reports,
        }


@dataclass
class PoolAccount:
    """An account in the smart pool."""
    account_id: str
    phone: str
    first_name: str = ""
    
    # Classification
    tier: AccountTier = AccountTier.FRESH
    state: AccountState = AccountState.AVAILABLE
    
    # Health
    health: AccountHealth = field(default_factory=AccountHealth)
    
    # Cooldowns
    cooldowns: List[AccountCooldown] = field(default_factory=list)
    
    # Usage tracking
    sessions_participated: int = 0
    targets_reported: List[str] = field(default_factory=list)  # Keep last 100
    
    # Timestamps
    added_at: float = field(default_factory=time.time)
    
    # Internal scoring for selection
    _selection_score: float = 0.0
    
    @property
    def age_days(self) -> float:
        return (time.time() - self.added_at) / 86400
    
    @property
    def is_available(self) -> bool:
        if self.state in [AccountState.BANNED, AccountState.DEAD, AccountState.WORKING]:
            return False
        if self.state == AccountState.RESTING and self.health.score < 30:
            return False
        # Check cooldowns
        self.cooldowns = [c for c in self.cooldowns if not c.is_expired]
        if self.cooldowns:
            return False
        return True
    
    @property
    def active_cooldown(self) -> Optional[AccountCooldown]:
        self.cooldowns = [c for c in self.cooldowns if not c.is_expired]
        return self.cooldowns[0] if self.cooldowns else None
    
    def has_reported_target(self, target: str) -> bool:
        return target in self.targets_reported
    
    def to_dict(self) -> Dict[str, Any]:
        cd = self.active_cooldown
        return {
            "account_id": self.account_id,
            "phone": self.phone,
            "first_name": self.first_name,
            "tier": self.tier.value,
            "state": self.state.value,
            "is_available": self.is_available,
            "health": self.health.to_dict(),
            "age_days": round(self.age_days, 1),
            "sessions": self.sessions_participated,
            "targets_reported": len(self.targets_reported),
            "cooldown": {
                "active": cd is not None,
                "reason": cd.reason.value if cd else None,
                "remaining_seconds": round(cd.remaining, 1) if cd else 0,
            },
        }


class AccountPoolManager:
    """
    Smart account pool with:
    - Health-based scoring and selection
    - Automatic cooling after usage
    - Tier-based daily limits
    - Risk assessment per account
    - Duplicate target prevention
    - Auto-rest for exhausted accounts
    - Optimal rotation strategy
    """
    
    POOL_FILE = Path("./data/account_pool.json")
    
    # Daily report limits by tier
    DAILY_LIMITS = {
        AccountTier.FRESH: 3,
        AccountTier.ROOKIE: 8,
        AccountTier.REGULAR: 15,
        AccountTier.VETERAN: 25,
        AccountTier.ELITE: 40,
    }
    
    # Cooldown durations by tier (seconds)
    COOLDOWN_DURATIONS = {
        AccountTier.FRESH: (120, 300),       # 2-5 min
        AccountTier.ROOKIE: (60, 180),       # 1-3 min
        AccountTier.REGULAR: (30, 120),      # 30s-2 min
        AccountTier.VETERAN: (20, 90),       # 20s-90s
        AccountTier.ELITE: (15, 60),         # 15s-60s
    }
    
    def __init__(self):
        self._pool: Dict[str, PoolAccount] = {}
        self._lock = asyncio.Lock()
        self._daily_usage: Dict[str, Dict[str, int]] = {}  # date -> {account_id: count}
        self._load_pool()
    
    def _load_pool(self):
        """Load pool from disk."""
        if self.POOL_FILE.exists():
            try:
                with open(self.POOL_FILE, 'r') as f:
                    data = json.load(f)
                    for p in data.get("accounts", []):
                        account = PoolAccount(
                            account_id=p["account_id"],
                            phone=p["phone"],
                            first_name=p.get("first_name", ""),
                            tier=AccountTier(p.get("tier", "fresh")),
                            state=AccountState(p.get("state", "available")),
                            added_at=p.get("added_at", time.time()),
                            sessions_participated=p.get("sessions", 0),
                            targets_reported=p.get("targets_reported", [])[-100:],
                        )
                        # Restore health
                        h = p.get("health", {})
                        account.health.score = h.get("score", 100)
                        account.health.total_reports = h.get("total_reports", 0)
                        account.health.successful_reports = h.get("successful", 0)
                        account.health.failed_reports = h.get("failed", 0)
                        account.health.flood_waits = h.get("flood_waits", 0)
                        account.health.last_used = h.get("last_used")
                        
                        # Fix state if was working (server restarted)
                        if account.state == AccountState.WORKING:
                            account.state = AccountState.AVAILABLE
                        
                        self._pool[account.account_id] = account
            except Exception as e:
                print(f"Error loading account pool: {e}")
    
    def _save_pool(self):
        """Save pool to disk."""
        self.POOL_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {
                "accounts": [],
                "updated_at": datetime.now().isoformat(),
            }
            for acc in self._pool.values():
                data["accounts"].append({
                    "account_id": acc.account_id,
                    "phone": acc.phone,
                    "first_name": acc.first_name,
                    "tier": acc.tier.value,
                    "state": acc.state.value,
                    "added_at": acc.added_at,
                    "sessions": acc.sessions_participated,
                    "targets_reported": acc.targets_reported[-100:],
                    "health": {
                        "score": acc.health.score,
                        "total_reports": acc.health.total_reports,
                        "successful": acc.health.successful_reports,
                        "failed": acc.health.failed_reports,
                        "flood_waits": acc.health.flood_waits,
                        "last_used": acc.health.last_used,
                    },
                })
            with open(self.POOL_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving account pool: {e}")
    
    # ==================== Account Registration ====================
    
    async def register_account(self, account_id: str, phone: str, first_name: str = "") -> PoolAccount:
        """Register a new account in the pool."""
        async with self._lock:
            if account_id in self._pool:
                return self._pool[account_id]
            
            account = PoolAccount(
                account_id=account_id,
                phone=phone,
                first_name=first_name,
            )
            
            self._update_tier(account)
            self._pool[account_id] = account
            self._save_pool()
            
            print(f"👤 Registered account {phone} | Tier: {account.tier.value}")
            return account
    
    async def sync_from_database(self):
        """Sync pool with database accounts."""
        accounts = await db.get_all_accounts()
        
        for acc in accounts:
            if acc['id'] not in self._pool:
                await self.register_account(
                    acc['id'],
                    acc['phone'],
                    acc.get('first_name', ''),
                )
            else:
                # Update name if changed
                pool_acc = self._pool[acc['id']]
                pool_acc.phone = acc['phone']
                pool_acc.first_name = acc.get('first_name', '')
        
        # Remove accounts that no longer exist
        db_ids = {acc['id'] for acc in accounts}
        to_remove = [aid for aid in self._pool if aid not in db_ids]
        for aid in to_remove:
            del self._pool[aid]
        
        self._save_pool()
    
    # ==================== Tier Management ====================
    
    def _update_tier(self, account: PoolAccount):
        """Update account tier based on age and usage."""
        age = account.age_days
        reports = account.health.total_reports
        
        if age >= 30 and reports >= 50:
            account.tier = AccountTier.ELITE
        elif age >= 14 and reports >= 20:
            account.tier = AccountTier.VETERAN
        elif age >= 7 and reports >= 5:
            account.tier = AccountTier.REGULAR
        elif age >= 3:
            account.tier = AccountTier.ROOKIE
        else:
            account.tier = AccountTier.FRESH
    
    # ==================== Health Management ====================
    
    def _recalculate_health(self, account: PoolAccount):
        """Recalculate account health score (0-100)."""
        h = account.health
        score = 100.0
        
        # Success rate penalty (up to -25)
        if h.total_reports >= 5:
            failure_rate = h.failed_reports / h.total_reports
            score -= failure_rate * 25
        
        # Flood wait penalty (up to -25)
        if h.flood_waits > 0:
            flood_penalty = min(h.flood_waits * 4, 25)
            score -= flood_penalty
        
        # Recent failures penalty (up to -20)
        if h.recent_failures > 3:
            score -= min((h.recent_failures - 3) * 5, 20)
        
        # Failure streak penalty (up to -15)
        if h.current_failure_streak >= 3:
            score -= min(h.current_failure_streak * 5, 15)
        
        # Recovery bonus (rested accounts heal)
        if h.hours_since_last_use > 6:
            hours_rested = min(h.hours_since_last_use - 6, 48)
            recovery = hours_rested * 0.5
            score += recovery
        
        # Success streak bonus
        if h.current_success_streak >= 5:
            score += min(h.current_success_streak, 10)
        
        # Cap score
        h.score = max(0, min(100, score))
        h.last_health_update = time.time()
    
    def _get_daily_usage(self, account_id: str) -> int:
        """Get today's usage count for an account."""
        today = datetime.now().strftime("%Y-%m-%d")
        return self._daily_usage.get(today, {}).get(account_id, 0)
    
    def _increment_daily_usage(self, account_id: str):
        """Increment today's usage count."""
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self._daily_usage:
            self._daily_usage = {today: {}}  # Reset old days
        self._daily_usage[today][account_id] = self._daily_usage[today].get(account_id, 0) + 1
    
    def _get_daily_remaining(self, account: PoolAccount) -> int:
        """Get remaining daily actions."""
        limit = self.DAILY_LIMITS.get(account.tier, 5)
        used = self._get_daily_usage(account.account_id)
        return max(0, limit - used)
    
    # ==================== Smart Selection ====================
    
    def _score_account(
        self,
        account: PoolAccount,
        target: str,
        prefer_fresh: bool = False,
    ) -> float:
        """
        Score an account for selection (higher = better choice).
        Considers health, cooldown, target history, daily usage, rest time.
        """
        if not account.is_available:
            return -999
        
        # Already reported this target? Disqualify.
        if account.has_reported_target(target):
            return -999
        
        # Daily limit reached? Disqualify.
        remaining = self._get_daily_remaining(account)
        if remaining <= 0:
            return -999
        
        score = 0.0
        
        # Health score (0-100 → 0-40 points)
        score += account.health.score * 0.4
        
        # Rest bonus (well-rested accounts are better)
        hours_rested = account.health.hours_since_last_use
        if hours_rested > 1:
            score += min(hours_rested * 2, 20)
        
        # Daily remaining capacity (more capacity = better)
        score += remaining * 1.5
        
        # Success streak bonus
        score += min(account.health.current_success_streak * 2, 10)
        
        # Failure streak penalty
        score -= account.health.current_failure_streak * 5
        
        # Tier bonus (higher tier = more trusted)
        tier_bonus = {
            AccountTier.FRESH: 0,
            AccountTier.ROOKIE: 3,
            AccountTier.REGULAR: 6,
            AccountTier.VETERAN: 10,
            AccountTier.ELITE: 15,
        }
        score += tier_bonus.get(account.tier, 0)
        
        # Prefer fresh accounts for variety (if requested)
        if prefer_fresh and account.health.total_reports < 10:
            score += 5
        
        # Diversity bonus (less used accounts get priority)
        if account.health.total_reports < 20:
            score += 5
        
        # Add randomness so selection isn't predictable
        score += random.uniform(-5, 5)
        
        return score
    
    async def select_accounts(
        self,
        target: str,
        count: int = 1,
        exclude: Optional[List[str]] = None,
        min_health: float = 30.0,
        prefer_fresh: bool = False,
    ) -> List[PoolAccount]:
        """
        Select the best accounts for an action.
        Returns accounts sorted by fitness score.
        """
        async with self._lock:
            exclude = exclude or []
            candidates = []
            
            for account in self._pool.values():
                if account.account_id in exclude:
                    continue
                if account.health.score < min_health:
                    continue
                
                score = self._score_account(account, target, prefer_fresh)
                if score > -999:
                    account._selection_score = score
                    candidates.append(account)
            
            # Sort by score (highest first)
            candidates.sort(key=lambda a: a._selection_score, reverse=True)
            
            return candidates[:count]
    
    async def select_best_account(
        self,
        target: str,
        exclude: Optional[List[str]] = None,
    ) -> Optional[PoolAccount]:
        """Select the single best account for a target."""
        accounts = await self.select_accounts(target, count=1, exclude=exclude)
        return accounts[0] if accounts else None
    
    # ==================== Usage Recording ====================
    
    async def record_usage(
        self,
        account_id: str,
        target: str,
        success: bool,
        flood_wait: int = 0,
        error: Optional[str] = None,
    ):
        """Record an account usage and update health."""
        async with self._lock:
            account = self._pool.get(account_id)
            if not account:
                return
            
            h = account.health
            h.total_reports += 1
            h.recent_reports += 1
            h.last_used = time.time()
            self._increment_daily_usage(account_id)
            
            if success:
                h.successful_reports += 1
                h.last_success = time.time()
                h.current_success_streak += 1
                h.current_failure_streak = 0
                h.best_success_streak = max(h.best_success_streak, h.current_success_streak)
            else:
                h.failed_reports += 1
                h.recent_failures += 1
                h.last_failure = time.time()
                h.current_failure_streak += 1
                h.current_success_streak = 0
                h.worst_failure_streak = max(h.worst_failure_streak, h.current_failure_streak)
                h.errors += 1
            
            if flood_wait > 0:
                h.flood_waits += 1
                h.recent_flood_waits += 1
                h.total_flood_wait_seconds += flood_wait
                h.last_flood_wait = time.time()
            
            # Record target
            if target not in account.targets_reported:
                account.targets_reported.append(target)
                if len(account.targets_reported) > 100:
                    account.targets_reported = account.targets_reported[-100:]
            
            # Recalculate health
            self._recalculate_health(account)
            self._update_tier(account)
            
            # Auto-apply cooldown
            await self._apply_post_action_cooldown(account, success, flood_wait)
            
            # Auto-rest if health is critical
            if h.score < 20:
                account.state = AccountState.RESTING
                print(f"   😰 Account {account.phone} sent to rest (health: {h.score:.0f})")
            
            self._save_pool()
    
    async def _apply_post_action_cooldown(
        self,
        account: PoolAccount,
        success: bool,
        flood_wait: int = 0,
    ):
        """Apply appropriate cooldown after an action."""
        if flood_wait > 0:
            # Flood wait: cooldown = flood_wait + buffer
            duration = flood_wait + random.uniform(30, 120)
            account.cooldowns.append(AccountCooldown(
                reason=CooldownReason.FLOOD_WAIT,
                started_at=time.time(),
                duration=duration,
            ))
            account.state = AccountState.COOLING
            return
        
        # Normal post-report cooldown (tier-based)
        cd_range = self.COOLDOWN_DURATIONS.get(account.tier, (60, 180))
        duration = random.uniform(*cd_range)
        
        # Failed actions get longer cooldown
        if not success:
            duration *= random.uniform(1.5, 2.5)
        
        # Consecutive failures get even longer
        if account.health.current_failure_streak >= 3:
            duration *= 2.0
        
        account.cooldowns.append(AccountCooldown(
            reason=CooldownReason.POST_REPORT if success else CooldownReason.ERROR_RECOVERY,
            started_at=time.time(),
            duration=duration,
        ))
        account.state = AccountState.COOLING
    
    # ==================== Account State Management ====================
    
    async def mark_working(self, account_id: str):
        """Mark account as currently working."""
        async with self._lock:
            if account_id in self._pool:
                self._pool[account_id].state = AccountState.WORKING
                self._save_pool()
    
    async def mark_available(self, account_id: str):
        """Mark account as available again."""
        async with self._lock:
            if account_id in self._pool:
                acc = self._pool[account_id]
                if acc.state == AccountState.WORKING:
                    acc.state = AccountState.AVAILABLE
                    self._save_pool()
    
    async def mark_banned(self, account_id: str):
        """Mark account as banned/restricted."""
        async with self._lock:
            if account_id in self._pool:
                self._pool[account_id].state = AccountState.BANNED
                self._pool[account_id].health.score = 0
                self._save_pool()
                print(f"   🚫 Account {self._pool[account_id].phone} marked as BANNED")
    
    async def rest_account(self, account_id: str, hours: float = 6):
        """Put account on extended rest."""
        async with self._lock:
            if account_id in self._pool:
                acc = self._pool[account_id]
                acc.state = AccountState.RESTING
                acc.cooldowns.append(AccountCooldown(
                    reason=CooldownReason.SCHEDULED_REST,
                    started_at=time.time(),
                    duration=hours * 3600,
                ))
                self._save_pool()
                print(f"   💤 Account {acc.phone} resting for {hours}h")
    
    async def wake_account(self, account_id: str):
        """Wake a resting account."""
        async with self._lock:
            if account_id in self._pool:
                acc = self._pool[account_id]
                if acc.state == AccountState.RESTING:
                    acc.state = AccountState.AVAILABLE
                    acc.cooldowns = []
                    # Partial health recovery from rest
                    acc.health.score = min(100, acc.health.score + 20)
                    self._save_pool()
    
    # ==================== Pool Analytics ====================
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get comprehensive pool statistics."""
        accounts = list(self._pool.values())
        
        if not accounts:
            return {
                "total": 0, "available": 0, "cooling": 0,
                "resting": 0, "working": 0, "banned": 0,
                "tiers": {}, "avg_health": 0,
            }
        
        # Update cooldowns
        for acc in accounts:
            acc.cooldowns = [c for c in acc.cooldowns if not c.is_expired]
            if acc.state == AccountState.COOLING and not acc.cooldowns:
                acc.state = AccountState.AVAILABLE
        
        # Count states
        state_counts = {}
        for state in AccountState:
            state_counts[state.value] = len([a for a in accounts if a.state == state])
        
        # Count tiers
        tier_counts = {}
        for tier in AccountTier:
            tier_counts[tier.value] = len([a for a in accounts if a.tier == tier])
        
        # Health stats
        health_scores = [a.health.score for a in accounts]
        avg_health = sum(health_scores) / len(health_scores)
        
        # Critical accounts
        critical = [a for a in accounts if a.health.score < 30]
        healthy = [a for a in accounts if a.health.score >= 70]
        
        return {
            "total": len(accounts),
            "available": state_counts.get("available", 0),
            "cooling": state_counts.get("cooling", 0),
            "resting": state_counts.get("resting", 0),
            "working": state_counts.get("working", 0),
            "banned": state_counts.get("banned", 0),
            "tiers": tier_counts,
            "avg_health": round(avg_health, 1),
            "critical_count": len(critical),
            "healthy_count": len(healthy),
            "total_reports": sum(a.health.total_reports for a in accounts),
            "total_success": sum(a.health.successful_reports for a in accounts),
        }
    
    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Get all accounts with full details."""
        # Update expired cooldowns first
        for acc in self._pool.values():
            acc.cooldowns = [c for c in acc.cooldowns if not c.is_expired]
            if acc.state == AccountState.COOLING and not acc.cooldowns:
                acc.state = AccountState.AVAILABLE
        
        return [a.to_dict() for a in sorted(
            self._pool.values(),
            key=lambda a: a.health.score,
            reverse=True,
        )]
    
    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get a single account's details."""
        acc = self._pool.get(account_id)
        return acc.to_dict() if acc else None
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get actionable recommendations for the account pool."""
        recs = []
        accounts = list(self._pool.values())
        
        # Accounts needing rest
        exhausted = [a for a in accounts if a.health.score < 30 and a.state != AccountState.RESTING]
        if exhausted:
            recs.append({
                "type": "rest_needed",
                "severity": "high",
                "message": f"{len(exhausted)} account(s) need rest",
                "accounts": [a.phone for a in exhausted],
            })
        
        # Low pool warning
        available = [a for a in accounts if a.is_available]
        if len(available) < 3:
            recs.append({
                "type": "low_pool",
                "severity": "high",
                "message": f"Only {len(available)} account(s) available. Add more or wait for cooldowns.",
            })
        
        # All fresh accounts warning
        fresh = [a for a in accounts if a.tier == AccountTier.FRESH]
        if len(fresh) == len(accounts) and accounts:
            recs.append({
                "type": "all_fresh",
                "severity": "medium",
                "message": "All accounts are fresh. Warm them up before heavy use.",
            })
        
        # Banned accounts
        banned = [a for a in accounts if a.state == AccountState.BANNED]
        if banned:
            recs.append({
                "type": "banned_accounts",
                "severity": "high",
                "message": f"{len(banned)} account(s) are banned. Replace them.",
                "accounts": [a.phone for a in banned],
            })
        
        # High flood wait rate
        flood_prone = [a for a in accounts if a.health.flood_waits > 3]
        if flood_prone:
            recs.append({
                "type": "flood_prone",
                "severity": "medium",
                "message": f"{len(flood_prone)} account(s) getting frequent flood waits. Increase delays.",
            })
        
        return recs


# Global instance
account_pool = AccountPoolManager()
