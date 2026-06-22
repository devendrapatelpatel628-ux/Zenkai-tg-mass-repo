"""
Anti-Detection Core v2
The brain of stealth operations. Coordinates all anti-detection measures.
"""

import asyncio
import random
import time
import hashlib
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

from stealth_config import (
    StealthLevel,
    StealthProfile,
    NetworkProfile,
    get_stealth_profile,
)
from network_simulator import NetworkSimulator
from fingerprint import fingerprint_generator, DeviceFingerprint


class RiskLevel(Enum):
    """Action risk assessment levels."""
    SAFE = "safe"           # 0-30: Proceed normally
    LOW = "low"             # 31-50: Proceed with caution
    MEDIUM = "medium"       # 51-70: Add extra delays
    HIGH = "high"           # 71-85: Consider skipping
    CRITICAL = "critical"   # 86-100: Abort/postpone


@dataclass
class ActionRecord:
    """Record of a performed action."""
    timestamp: float
    action_type: str
    account_id: str
    target: str
    success: bool
    risk_score: int
    delay_used: float
    fingerprint_hash: str
    network_type: str


@dataclass
class SessionContext:
    """Tracks the current session state for anti-detection."""
    session_id: str
    stealth_profile: StealthProfile
    fingerprint: DeviceFingerprint
    network_sim: NetworkSimulator
    
    # Session tracking
    started_at: float = field(default_factory=time.time)
    action_count: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    total_delay_seconds: float = 0.0
    
    # Pattern tracking (rolling window)
    recent_delays: deque = field(default_factory=lambda: deque(maxlen=20))
    recent_actions: deque = field(default_factory=lambda: deque(maxlen=50))
    
    # Account usage tracking
    account_action_counts: Dict[str, int] = field(default_factory=dict)
    account_last_used: Dict[str, float] = field(default_factory=dict)
    account_cooldowns: Dict[str, float] = field(default_factory=dict)
    
    # Risk state
    current_risk_level: RiskLevel = RiskLevel.SAFE
    risk_score: int = 0
    is_paused: bool = False
    should_abort: bool = False
    
    @property
    def session_duration(self) -> float:
        """Session duration in seconds."""
        return time.time() - self.started_at
    
    @property
    def session_duration_minutes(self) -> float:
        """Session duration in minutes."""
        return self.session_duration / 60
    
    @property
    def avg_delay(self) -> float:
        """Average delay between actions."""
        if not self.recent_delays:
            return 0.0
        return sum(self.recent_delays) / len(self.recent_delays)


class AntiDetectionEngine:
    """
    Core anti-detection engine that coordinates:
    - Risk assessment
    - Timing control
    - Pattern variation
    - Device consistency
    - Session management
    - Account rotation
    """
    
    def __init__(self):
        self._active_sessions: Dict[str, SessionContext] = {}
        self._global_action_history: deque = deque(maxlen=1000)
        self._account_global_usage: Dict[str, List[float]] = {}
        self._target_report_history: Dict[str, List[Dict]] = {}
    
    # ==================== Session Management ====================
    
    def create_session(
        self,
        session_id: str,
        stealth_level: StealthLevel = StealthLevel.STEALTH,
    ) -> SessionContext:
        """Create a new anti-detection session."""
        profile = get_stealth_profile(stealth_level)
        fingerprint = fingerprint_generator.generate_random_fingerprint()
        network_type = NetworkSimulator.random_profile()
        network_sim = NetworkSimulator(network_type)
        
        ctx = SessionContext(
            session_id=session_id,
            stealth_profile=profile,
            fingerprint=fingerprint,
            network_sim=network_sim,
        )
        
        self._active_sessions[session_id] = ctx
        
        print(f"🛡️ Anti-Detection Session Created")
        print(f"   Level: {stealth_level.value}")
        print(f"   Device: {fingerprint.device_model}")
        print(f"   App: {fingerprint.app_name} {fingerprint.app_version}")
        print(f"   Network: {network_type.value}")
        print(f"   Max duration: {profile.max_session_duration_minutes}min")
        
        return ctx
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Get an active session context."""
        return self._active_sessions.get(session_id)
    
    def end_session(self, session_id: str):
        """End a session and clean up."""
        if session_id in self._active_sessions:
            ctx = self._active_sessions[session_id]
            duration = ctx.session_duration
            print(f"🛡️ Session {session_id} ended after {duration:.0f}s ({ctx.action_count} actions)")
            del self._active_sessions[session_id]
    
    # ==================== Risk Assessment ====================
    
    def assess_risk(
        self,
        ctx: SessionContext,
        account_id: str,
        target: str,
        action_type: str = "report",
    ) -> Tuple[int, RiskLevel, List[str]]:
        """
        Assess the risk of performing an action.
        Returns: (risk_score, risk_level, risk_factors)
        """
        score = 0
        factors = []
        
        # Factor 1: Session duration (longer = riskier)
        duration_mins = ctx.session_duration_minutes
        if duration_mins > ctx.stealth_profile.max_session_duration_minutes:
            score += 30
            factors.append(f"Session too long ({duration_mins:.0f}min)")
        elif duration_mins > ctx.stealth_profile.max_session_duration_minutes * 0.8:
            score += 15
            factors.append(f"Session nearing limit ({duration_mins:.0f}min)")
        
        # Factor 2: Action volume
        if ctx.action_count > ctx.stealth_profile.max_actions_before_long_break:
            score += 20
            factors.append(f"High action volume ({ctx.action_count})")
        elif ctx.action_count > ctx.stealth_profile.max_actions_before_long_break * 0.7:
            score += 10
            factors.append("Approaching action limit")
        
        # Factor 3: Consecutive failures
        if ctx.consecutive_failures >= ctx.stealth_profile.max_consecutive_failures:
            score += 30
            factors.append(f"Too many failures ({ctx.consecutive_failures} in a row)")
        elif ctx.consecutive_failures >= 3:
            score += 15
            factors.append(f"Multiple failures ({ctx.consecutive_failures})")
        
        # Factor 4: Account overuse
        account_actions = ctx.account_action_counts.get(account_id, 0)
        if account_actions > 10:
            score += 20
            factors.append(f"Account overused ({account_actions} actions)")
        elif account_actions > 5:
            score += 10
            factors.append(f"Account moderately used ({account_actions})")
        
        # Factor 5: Account cooldown
        last_used = ctx.account_last_used.get(account_id, 0)
        time_since = time.time() - last_used
        if time_since < 30 and last_used > 0:
            score += 15
            factors.append(f"Account used too recently ({time_since:.0f}s ago)")
        
        # Factor 6: Target already reported by same account
        target_history = self._target_report_history.get(target, [])
        already_reported = any(
            h.get("account_id") == account_id 
            for h in target_history
        )
        if already_reported:
            score += 25
            factors.append("Target already reported by this account")
        
        # Factor 7: Time of day risk
        hour = datetime.now().hour
        if 2 <= hour <= 5:
            score += 5
            factors.append("Low traffic hours (unusual activity)")
        
        # Factor 8: Delay pattern regularity
        if len(ctx.recent_delays) >= 5:
            delays = list(ctx.recent_delays)
            avg = sum(delays) / len(delays)
            variance = sum((d - avg) ** 2 for d in delays) / len(delays)
            std_dev = math.sqrt(variance)
            cv = std_dev / avg if avg > 0 else 0
            
            if cv < 0.15:  # Too regular (< 15% variation)
                score += 10
                factors.append("Delay pattern too regular")
        
        # Factor 9: Global rate limiting
        global_recent = [
            a for a in self._global_action_history 
            if time.time() - a.timestamp < 300  # Last 5 minutes
        ]
        if len(global_recent) > 20:
            score += 15
            factors.append(f"High global action rate ({len(global_recent)} in 5min)")
        
        # Determine risk level
        if score <= 30:
            level = RiskLevel.SAFE
        elif score <= 50:
            level = RiskLevel.LOW
        elif score <= 70:
            level = RiskLevel.MEDIUM
        elif score <= 85:
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.CRITICAL
        
        ctx.risk_score = score
        ctx.current_risk_level = level
        
        return score, level, factors
    
    # ==================== Timing Control ====================
    
    async def wait_action_delay(
        self,
        ctx: SessionContext,
        risk_score: int = 0,
    ) -> float:
        """
        Calculate and wait for the optimal delay between actions.
        Considers stealth profile, risk, fatigue, and time of day.
        """
        profile = ctx.stealth_profile
        
        # Base delay from profile
        base_delay = random.uniform(
            profile.min_action_delay,
            profile.max_action_delay
        )
        
        # Apply fatigue multiplier
        if profile.fatigue_enabled and ctx.action_count >= profile.fatigue_start_after:
            fatigue_factor = 1.0 + (
                (ctx.action_count - profile.fatigue_start_after) / 30
            ) * profile.fatigue_slowdown_factor
            fatigue_factor = min(fatigue_factor, 2.5)  # Cap at 2.5x
            base_delay *= fatigue_factor
        
        # Apply risk multiplier
        if risk_score > 50:
            risk_factor = 1.0 + (risk_score - 50) / 100
            base_delay *= risk_factor
        
        # Apply time-of-day modifier
        hour = datetime.now().hour
        if 23 <= hour or hour < 6:
            base_delay *= random.uniform(1.2, 1.8)  # Slower at night
        elif 6 <= hour < 9:
            base_delay *= random.uniform(0.9, 1.1)  # Normal morning
        elif 12 <= hour < 14:
            base_delay *= random.uniform(1.1, 1.3)  # Lunch = slower
        
        # Add jitter to prevent pattern detection
        if profile.jitter_enabled:
            jitter_range = base_delay * 0.3
            jitter = random.uniform(-jitter_range, jitter_range)
            base_delay += jitter
        
        # Network latency simulation
        if ctx.network_sim:
            await ctx.network_sim.simulate_request_latency()
        
        # Ensure minimum delay
        base_delay = max(1.0, base_delay)
        
        # Record delay for pattern analysis
        ctx.recent_delays.append(base_delay)
        ctx.total_delay_seconds += base_delay
        
        # Actually wait
        await asyncio.sleep(base_delay)
        
        return base_delay
    
    async def wait_think_delay(self, ctx: SessionContext) -> float:
        """Simulate "thinking" before an action."""
        profile = ctx.stealth_profile
        
        delay = random.uniform(profile.min_think_delay, profile.max_think_delay)
        
        # Sometimes longer think pauses (human distraction)
        if random.random() < 0.1:
            delay += random.uniform(1.0, 5.0)
        
        await asyncio.sleep(delay)
        return delay
    
    async def maybe_take_break(self, ctx: SessionContext) -> float:
        """Maybe take a break based on probability and fatigue."""
        profile = ctx.stealth_profile
        
        # Check if we need a long break (exceeded action limit)
        if ctx.action_count >= profile.max_actions_before_long_break:
            break_duration = random.uniform(*profile.long_break_range)
            print(f"   😴 Long break: {break_duration:.0f}s (action limit reached)")
            await asyncio.sleep(break_duration)
            ctx.action_count = max(0, ctx.action_count - 10)  # Reset some fatigue
            return break_duration
        
        # Random break based on probability
        if random.random() < profile.break_probability:
            break_duration = random.uniform(*profile.break_duration_range)
            print(f"   ☕ Natural break: {break_duration:.0f}s")
            await asyncio.sleep(break_duration)
            return break_duration
        
        return 0.0
    
    def should_skip_action(self, ctx: SessionContext) -> bool:
        """Determine if we should skip this action (human-like imperfection)."""
        return random.random() < ctx.stealth_profile.skip_probability
    
    # ==================== Device Management ====================
    
    def get_consistent_fingerprint(self, ctx: SessionContext) -> DeviceFingerprint:
        """
        Get device fingerprint with consistency checks.
        Same device within a session, different across sessions.
        """
        return ctx.fingerprint
    
    def validate_fingerprint_consistency(self, fp: DeviceFingerprint) -> Tuple[bool, List[str]]:
        """
        Validate that a fingerprint is internally consistent.
        No Android device with iOS app, etc.
        """
        issues = []
        
        # Check device-OS consistency
        android_brands = ["Samsung", "Google", "OnePlus", "Xiaomi", "OPPO", "Vivo", 
                         "Realme", "Huawei", "Nothing", "ASUS", "Sony", "Motorola"]
        ios_names = ["iPhone", "iPad"]
        
        is_android = any(brand in fp.device_model for brand in android_brands)
        is_ios = any(name in fp.device_model for name in ios_names)
        
        # Check app-device consistency
        android_apps = ["Telegram Android", "Nicegram", "Plus Messenger", "Telegram X",
                       "Nekogram", "BGram", "Turbo Telegram", "Vidogram", "Graph Messenger"]
        ios_apps = ["Telegram iOS"]
        
        is_android_app = fp.app_name in android_apps
        is_ios_app = fp.app_name in ios_apps
        
        if is_android and is_ios_app:
            issues.append("Android device with iOS app")
        
        if is_ios and is_android_app:
            issues.append("iOS device with Android app")
        
        # Check SDK version consistency
        if is_android and "SDK" not in fp.system_version:
            issues.append("Android device without SDK version")
        
        if is_ios and "SDK" in fp.system_version:
            issues.append("iOS device with Android SDK version")
        
        return len(issues) == 0, issues
    
    # ==================== Account Management ====================
    
    def select_best_account(
        self,
        ctx: SessionContext,
        available_accounts: List[str],
        target: str,
    ) -> Optional[str]:
        """
        Select the best account for the next action.
        Considers usage, cooldown, and risk.
        """
        candidates = []
        
        for account_id in available_accounts:
            # Check cooldown
            cooldown_until = ctx.account_cooldowns.get(account_id, 0)
            if time.time() < cooldown_until:
                continue
            
            # Check if already reported this target
            target_history = self._target_report_history.get(target, [])
            already_reported = any(
                h.get("account_id") == account_id for h in target_history
            )
            if already_reported:
                continue
            
            # Calculate account score (lower = better)
            action_count = ctx.account_action_counts.get(account_id, 0)
            last_used = ctx.account_last_used.get(account_id, 0)
            time_since = time.time() - last_used if last_used > 0 else 999
            
            score = action_count * 10 - time_since * 0.1
            
            candidates.append((account_id, score))
        
        if not candidates:
            return None
        
        # Sort by score (lower = better) and add randomness
        candidates.sort(key=lambda x: x[1])
        
        # Don't always pick the "best" - add randomness
        if len(candidates) >= 3:
            # Pick from top 3 randomly
            top = candidates[:3]
            return random.choice(top)[0]
        else:
            return candidates[0][0]
    
    def record_account_usage(
        self,
        ctx: SessionContext,
        account_id: str,
        cooldown_seconds: float = 30.0,
    ):
        """Record that an account was used."""
        ctx.account_action_counts[account_id] = (
            ctx.account_action_counts.get(account_id, 0) + 1
        )
        ctx.account_last_used[account_id] = time.time()
        ctx.account_cooldowns[account_id] = time.time() + cooldown_seconds
        
        # Global tracking
        if account_id not in self._account_global_usage:
            self._account_global_usage[account_id] = []
        self._account_global_usage[account_id].append(time.time())
    
    # ==================== Action Recording ====================
    
    def record_action(
        self,
        ctx: SessionContext,
        action_type: str,
        account_id: str,
        target: str,
        success: bool,
        delay_used: float,
    ):
        """Record an action for pattern analysis."""
        record = ActionRecord(
            timestamp=time.time(),
            action_type=action_type,
            account_id=account_id,
            target=target,
            success=success,
            risk_score=ctx.risk_score,
            delay_used=delay_used,
            fingerprint_hash=hashlib.md5(
                ctx.fingerprint.device_model.encode()
            ).hexdigest()[:8],
            network_type=ctx.network_sim._state.profile.value,
        )
        
        ctx.recent_actions.append(record)
        ctx.action_count += 1
        self._global_action_history.append(record)
        
        # Track target history
        if target not in self._target_report_history:
            self._target_report_history[target] = []
        self._target_report_history[target].append({
            "account_id": account_id,
            "timestamp": time.time(),
            "success": success,
        })
        
        # Update consecutive counts
        if success:
            ctx.consecutive_successes += 1
            ctx.consecutive_failures = 0
        else:
            ctx.consecutive_failures += 1
            ctx.consecutive_successes = 0
    
    # ==================== Session Checks ====================
    
    def should_end_session(self, ctx: SessionContext) -> Tuple[bool, str]:
        """Check if the session should be ended for safety."""
        profile = ctx.stealth_profile
        
        # Check session duration
        if ctx.session_duration_minutes >= profile.max_session_duration_minutes:
            return True, "Session duration limit reached"
        
        # Check consecutive failures
        if ctx.consecutive_failures >= profile.max_consecutive_failures:
            return True, f"Too many consecutive failures ({ctx.consecutive_failures})"
        
        # Check risk level
        if ctx.risk_score > profile.max_risk_score:
            return True, f"Risk score too high ({ctx.risk_score})"
        
        # Check if abort flag set
        if ctx.should_abort:
            return True, "Session abort requested"
        
        return False, ""
    
    async def simulate_pre_action_behavior(
        self,
        ctx: SessionContext,
        target: str,
    ) -> float:
        """
        Simulate what a real human does BEFORE reporting:
        - Load the profile
        - Read some content
        - Scroll a bit
        - Then report
        """
        total_time = 0.0
        
        # Simulate opening/loading the target's page
        load_time = await ctx.network_sim.simulate_page_load()
        total_time += load_time
        
        # Simulate reading the profile/content
        reading_time = await ctx.network_sim.simulate_reading_time(
            random.randint(50, 200)  # Random content length
        )
        total_time += reading_time
        
        # Sometimes scroll through content
        if random.random() < 0.4:
            scroll_time = await ctx.network_sim.simulate_scrolling(
                random.randint(2, 5)
            )
            total_time += scroll_time
        
        return total_time
    
    # ==================== Stats & Info ====================
    
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed session statistics."""
        ctx = self._active_sessions.get(session_id)
        if not ctx:
            return None
        
        return {
            "session_id": session_id,
            "stealth_level": ctx.stealth_profile.level.value,
            "duration_seconds": round(ctx.session_duration, 1),
            "action_count": ctx.action_count,
            "risk_score": ctx.risk_score,
            "risk_level": ctx.current_risk_level.value,
            "avg_delay": round(ctx.avg_delay, 2),
            "consecutive_failures": ctx.consecutive_failures,
            "total_delay": round(ctx.total_delay_seconds, 1),
            "fingerprint": {
                "device": ctx.fingerprint.device_model,
                "app": ctx.fingerprint.app_name,
                "version": ctx.fingerprint.app_version,
            },
            "network": ctx.network_sim.get_stats(),
        }
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global anti-detection statistics."""
        total_actions = len(self._global_action_history)
        recent_actions = [
            a for a in self._global_action_history
            if time.time() - a.timestamp < 3600  # Last hour
        ]
        
        return {
            "active_sessions": len(self._active_sessions),
            "total_actions_tracked": total_actions,
            "actions_last_hour": len(recent_actions),
            "unique_targets": len(self._target_report_history),
            "accounts_tracked": len(self._account_global_usage),
        }


# Global instance
anti_detection = AntiDetectionEngine()
