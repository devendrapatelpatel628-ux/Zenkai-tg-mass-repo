"""
Stealth Configuration
Defines protection levels and behavioral parameters
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Tuple
import random


class StealthLevel(Enum):
    """Protection levels - higher = safer but slower."""
    NORMAL = "normal"
    STEALTH = "stealth"
    PARANOID = "paranoid"


class NetworkProfile(Enum):
    """Simulated network types."""
    WIFI = "wifi"
    LTE_4G = "4g"
    MOBILE_3G = "3g"
    MOBILE_5G = "5g"
    ETHERNET = "ethernet"


@dataclass
class StealthProfile:
    """Complete stealth behavior configuration."""
    level: StealthLevel
    
    # Timing
    min_action_delay: float = 2.0
    max_action_delay: float = 8.0
    min_think_delay: float = 0.3
    max_think_delay: float = 2.0
    break_probability: float = 0.05
    break_duration_range: Tuple[float, float] = (10.0, 60.0)
    skip_probability: float = 0.02
    
    # Fatigue
    fatigue_enabled: bool = True
    fatigue_start_after: int = 10
    fatigue_slowdown_factor: float = 0.3
    max_actions_before_long_break: int = 25
    long_break_range: Tuple[float, float] = (30.0, 120.0)
    
    # Session
    max_session_duration_minutes: int = 45
    rotate_device_every_n_actions: int = 0  # 0 = per session
    jitter_enabled: bool = True
    
    # Network simulation
    network_profile: NetworkProfile = NetworkProfile.LTE_4G
    simulate_connection_drops: bool = False
    connection_drop_probability: float = 0.01
    
    # Error simulation
    retry_probability: float = 0.0
    double_action_probability: float = 0.0
    
    # Risk thresholds
    max_risk_score: int = 70
    abort_on_flood_wait: bool = False
    max_consecutive_failures: int = 5


# Pre-configured stealth profiles
STEALTH_PROFILES: Dict[StealthLevel, StealthProfile] = {
    
    StealthLevel.NORMAL: StealthProfile(
        level=StealthLevel.NORMAL,
        min_action_delay=2.0,
        max_action_delay=6.0,
        min_think_delay=0.2,
        max_think_delay=1.0,
        break_probability=0.03,
        break_duration_range=(5.0, 20.0),
        skip_probability=0.01,
        fatigue_enabled=True,
        fatigue_start_after=15,
        fatigue_slowdown_factor=0.2,
        max_actions_before_long_break=40,
        long_break_range=(15.0, 45.0),
        max_session_duration_minutes=60,
        rotate_device_every_n_actions=0,
        jitter_enabled=True,
        network_profile=NetworkProfile.LTE_4G,
        simulate_connection_drops=False,
        max_risk_score=80,
        abort_on_flood_wait=False,
        max_consecutive_failures=8,
    ),
    
    StealthLevel.STEALTH: StealthProfile(
        level=StealthLevel.STEALTH,
        min_action_delay=3.0,
        max_action_delay=10.0,
        min_think_delay=0.5,
        max_think_delay=2.5,
        break_probability=0.08,
        break_duration_range=(10.0, 60.0),
        skip_probability=0.03,
        fatigue_enabled=True,
        fatigue_start_after=8,
        fatigue_slowdown_factor=0.4,
        max_actions_before_long_break=20,
        long_break_range=(30.0, 90.0),
        max_session_duration_minutes=40,
        rotate_device_every_n_actions=0,
        jitter_enabled=True,
        network_profile=NetworkProfile.LTE_4G,
        simulate_connection_drops=True,
        connection_drop_probability=0.02,
        retry_probability=0.03,
        double_action_probability=0.01,
        max_risk_score=65,
        abort_on_flood_wait=True,
        max_consecutive_failures=4,
    ),
    
    StealthLevel.PARANOID: StealthProfile(
        level=StealthLevel.PARANOID,
        min_action_delay=5.0,
        max_action_delay=18.0,
        min_think_delay=1.0,
        max_think_delay=4.0,
        break_probability=0.12,
        break_duration_range=(20.0, 120.0),
        skip_probability=0.05,
        fatigue_enabled=True,
        fatigue_start_after=5,
        fatigue_slowdown_factor=0.6,
        max_actions_before_long_break=12,
        long_break_range=(60.0, 300.0),
        max_session_duration_minutes=25,
        rotate_device_every_n_actions=0,
        jitter_enabled=True,
        network_profile=NetworkProfile.MOBILE_3G,
        simulate_connection_drops=True,
        connection_drop_probability=0.05,
        retry_probability=0.05,
        double_action_probability=0.02,
        max_risk_score=50,
        abort_on_flood_wait=True,
        max_consecutive_failures=2,
    ),
}


def get_stealth_profile(level: StealthLevel) -> StealthProfile:
    """Get a stealth profile with slight random variations."""
    base = STEALTH_PROFILES[level]
    
    # Apply slight random variations so no two runs are identical
    profile = StealthProfile(
        level=base.level,
        min_action_delay=base.min_action_delay * random.uniform(0.85, 1.15),
        max_action_delay=base.max_action_delay * random.uniform(0.85, 1.15),
        min_think_delay=base.min_think_delay * random.uniform(0.8, 1.2),
        max_think_delay=base.max_think_delay * random.uniform(0.8, 1.2),
        break_probability=base.break_probability * random.uniform(0.7, 1.3),
        break_duration_range=(
            base.break_duration_range[0] * random.uniform(0.8, 1.2),
            base.break_duration_range[1] * random.uniform(0.8, 1.2),
        ),
        skip_probability=base.skip_probability * random.uniform(0.6, 1.4),
        fatigue_enabled=base.fatigue_enabled,
        fatigue_start_after=max(3, base.fatigue_start_after + random.randint(-2, 2)),
        fatigue_slowdown_factor=base.fatigue_slowdown_factor * random.uniform(0.8, 1.2),
        max_actions_before_long_break=max(5, base.max_actions_before_long_break + random.randint(-3, 3)),
        long_break_range=(
            base.long_break_range[0] * random.uniform(0.8, 1.2),
            base.long_break_range[1] * random.uniform(0.8, 1.2),
        ),
        max_session_duration_minutes=base.max_session_duration_minutes + random.randint(-5, 5),
        rotate_device_every_n_actions=base.rotate_device_every_n_actions,
        jitter_enabled=base.jitter_enabled,
        network_profile=base.network_profile,
        simulate_connection_drops=base.simulate_connection_drops,
        connection_drop_probability=base.connection_drop_probability,
        retry_probability=base.retry_probability,
        double_action_probability=base.double_action_probability,
        max_risk_score=base.max_risk_score,
        abort_on_flood_wait=base.abort_on_flood_wait,
        max_consecutive_failures=base.max_consecutive_failures,
    )
    
    return profile
