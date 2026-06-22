"""
Network Latency & Behavior Simulator
Mimics real mobile/wifi network patterns to avoid timing-based detection
"""

import asyncio
import random
import math
import time
from typing import Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from stealth_config import NetworkProfile


@dataclass
class NetworkState:
    """Tracks simulated network state."""
    profile: NetworkProfile
    signal_strength: float = 1.0  # 0.0 to 1.0
    is_connected: bool = True
    last_request_time: float = 0.0
    total_requests: int = 0
    total_latency_ms: float = 0.0
    drops_count: int = 0
    
    # Rolling signal that changes over time
    _signal_phase: float = field(default_factory=lambda: random.uniform(0, 2 * math.pi))
    _signal_frequency: float = field(default_factory=lambda: random.uniform(0.001, 0.01))
    
    def update_signal(self):
        """Update signal strength with natural oscillation."""
        t = time.time()
        # Sine wave with noise for natural signal variation
        base = 0.5 + 0.3 * math.sin(t * self._signal_frequency + self._signal_phase)
        noise = random.gauss(0, 0.05)
        self.signal_strength = max(0.1, min(1.0, base + noise))


# Network latency profiles (milliseconds)
NETWORK_LATENCIES = {
    NetworkProfile.WIFI: {
        "base_latency": (3, 15),
        "jitter": (0, 8),
        "packet_loss_rate": 0.001,
        "burst_probability": 0.02,
        "burst_latency": (50, 200),
        "dns_lookup": (5, 30),
        "tcp_handshake": (10, 40),
        "tls_handshake": (15, 50),
        "signal_impact": 0.2,  # Low impact of signal on WiFi
    },
    NetworkProfile.MOBILE_5G: {
        "base_latency": (8, 30),
        "jitter": (2, 12),
        "packet_loss_rate": 0.005,
        "burst_probability": 0.03,
        "burst_latency": (80, 300),
        "dns_lookup": (10, 50),
        "tcp_handshake": (15, 60),
        "tls_handshake": (20, 80),
        "signal_impact": 0.4,
    },
    NetworkProfile.LTE_4G: {
        "base_latency": (20, 80),
        "jitter": (5, 30),
        "packet_loss_rate": 0.01,
        "burst_probability": 0.05,
        "burst_latency": (100, 500),
        "dns_lookup": (20, 80),
        "tcp_handshake": (30, 100),
        "tls_handshake": (40, 120),
        "signal_impact": 0.6,
    },
    NetworkProfile.MOBILE_3G: {
        "base_latency": (80, 300),
        "jitter": (20, 100),
        "packet_loss_rate": 0.03,
        "burst_probability": 0.08,
        "burst_latency": (200, 1500),
        "dns_lookup": (50, 200),
        "tcp_handshake": (80, 300),
        "tls_handshake": (100, 400),
        "signal_impact": 0.8,
    },
    NetworkProfile.ETHERNET: {
        "base_latency": (1, 5),
        "jitter": (0, 2),
        "packet_loss_rate": 0.0001,
        "burst_probability": 0.005,
        "burst_latency": (10, 50),
        "dns_lookup": (2, 10),
        "tcp_handshake": (3, 15),
        "tls_handshake": (5, 20),
        "signal_impact": 0.0,
    },
}


class NetworkSimulator:
    """
    Simulates realistic network behavior:
    - Variable latency based on network type
    - Signal strength fluctuations
    - Packet loss simulation
    - Connection drops
    - DNS/TCP/TLS handshake delays
    - Network condition changes over time
    """
    
    def __init__(self, profile: NetworkProfile = NetworkProfile.LTE_4G):
        self._state = NetworkState(profile=profile)
        self._config = NETWORK_LATENCIES.get(profile, NETWORK_LATENCIES[NetworkProfile.LTE_4G])
        self._session_start = time.time()
    
    def set_profile(self, profile: NetworkProfile):
        """Change network profile mid-session."""
        self._state.profile = profile
        self._config = NETWORK_LATENCIES.get(profile, NETWORK_LATENCIES[NetworkProfile.LTE_4G])
    
    def _calculate_latency(self) -> float:
        """Calculate realistic latency in milliseconds."""
        # Update signal
        self._state.update_signal()
        
        # Base latency
        base_min, base_max = self._config["base_latency"]
        latency = random.uniform(base_min, base_max)
        
        # Apply signal strength impact
        signal_impact = self._config["signal_impact"]
        signal_factor = 1.0 + (1.0 - self._state.signal_strength) * signal_impact * 2
        latency *= signal_factor
        
        # Add jitter
        jitter_min, jitter_max = self._config["jitter"]
        jitter = random.uniform(jitter_min, jitter_max)
        if random.random() < 0.5:
            jitter = -jitter * 0.3  # Sometimes negative jitter (faster)
        latency += jitter
        
        # Occasional burst latency (congestion simulation)
        if random.random() < self._config["burst_probability"]:
            burst_min, burst_max = self._config["burst_latency"]
            latency += random.uniform(burst_min, burst_max)
        
        # Time-based patterns (networks are slower during peak hours)
        hour = datetime.now().hour
        if 8 <= hour <= 10 or 17 <= hour <= 20:  # Rush hours
            latency *= random.uniform(1.1, 1.4)
        elif 2 <= hour <= 5:  # Low traffic
            latency *= random.uniform(0.8, 0.95)
        
        return max(1.0, latency)
    
    def _calculate_first_request_latency(self) -> float:
        """Calculate latency for first request (includes DNS + TCP + TLS)."""
        latency = self._calculate_latency()
        
        # DNS lookup
        dns_min, dns_max = self._config["dns_lookup"]
        latency += random.uniform(dns_min, dns_max)
        
        # TCP handshake
        tcp_min, tcp_max = self._config["tcp_handshake"]
        latency += random.uniform(tcp_min, tcp_max)
        
        # TLS handshake
        tls_min, tls_max = self._config["tls_handshake"]
        latency += random.uniform(tls_min, tls_max)
        
        return latency
    
    async def simulate_request_latency(self, is_first: bool = False) -> float:
        """
        Simulate network latency for a request.
        Returns: actual delay in seconds
        """
        if is_first:
            latency_ms = self._calculate_first_request_latency()
        else:
            latency_ms = self._calculate_latency()
        
        # Check for packet loss (retry adds latency)
        if random.random() < self._config["packet_loss_rate"]:
            # Packet lost, simulate retry after timeout
            timeout_ms = random.uniform(500, 2000)
            latency_ms += timeout_ms
            self._state.drops_count += 1
        
        # Convert to seconds
        delay_seconds = latency_ms / 1000.0
        
        # Track stats
        self._state.total_requests += 1
        self._state.total_latency_ms += latency_ms
        self._state.last_request_time = time.time()
        
        # Actually wait
        await asyncio.sleep(delay_seconds)
        
        return delay_seconds
    
    async def simulate_connection_drop(self) -> float:
        """
        Simulate a connection drop and reconnection.
        Returns: total downtime in seconds
        """
        self._state.is_connected = False
        
        # Disconnect duration (1-10 seconds typically)
        disconnect_time = random.uniform(1.0, 10.0)
        
        # Worse signal = longer disconnect
        disconnect_time *= (1.0 + (1.0 - self._state.signal_strength) * 2)
        
        print(f"   📡 Connection dropped! Reconnecting in {disconnect_time:.1f}s...")
        await asyncio.sleep(disconnect_time)
        
        # Reconnection handshake
        reconnect_time = self._calculate_first_request_latency() / 1000.0
        await asyncio.sleep(reconnect_time)
        
        self._state.is_connected = True
        self._state.drops_count += 1
        
        total = disconnect_time + reconnect_time
        print(f"   📡 Reconnected! (was offline {total:.1f}s)")
        
        return total
    
    async def simulate_typing_delay(self, text_length: int) -> float:
        """
        Simulate the time it takes to type a message.
        Based on average typing speed with variations.
        """
        # Average typing speed: 30-60 WPM
        # Average word = 5 chars, so 150-300 chars per minute
        # = 2.5-5 chars per second
        
        wpm = random.uniform(25, 55)  # Words per minute
        chars_per_second = (wpm * 5) / 60
        
        # Base typing time
        typing_time = text_length / chars_per_second
        
        # Add pauses for thinking (every 20-50 chars)
        num_pauses = text_length // random.randint(20, 50)
        for _ in range(num_pauses):
            typing_time += random.uniform(0.5, 3.0)
        
        # Add backspace/correction time (10% of chars get "corrected")
        corrections = int(text_length * random.uniform(0.05, 0.15))
        typing_time += corrections * random.uniform(0.2, 0.5)
        
        # Cap at reasonable amount
        typing_time = min(typing_time, 120.0)
        
        # Actually wait (but not the full time, simulate background typing)
        actual_wait = typing_time * random.uniform(0.3, 0.6)
        await asyncio.sleep(actual_wait)
        
        return actual_wait
    
    async def simulate_reading_time(self, content_length: int) -> float:
        """
        Simulate time to read content.
        Average reading speed: 200-300 WPM
        """
        # Words from character count
        word_count = content_length / 5
        
        # Reading speed
        wpm = random.uniform(180, 350)
        reading_time = (word_count / wpm) * 60  # seconds
        
        # Add comprehension pauses
        reading_time *= random.uniform(1.0, 1.5)
        
        # Minimum reading time
        reading_time = max(0.5, min(reading_time, 30.0))
        
        await asyncio.sleep(reading_time)
        
        return reading_time
    
    async def simulate_page_load(self) -> float:
        """Simulate loading a page/dialog."""
        # Network latency
        latency = await self.simulate_request_latency()
        
        # Rendering time
        render_time = random.uniform(0.1, 0.8)
        await asyncio.sleep(render_time)
        
        return latency + render_time
    
    async def simulate_scrolling(self, items: int = 5) -> float:
        """Simulate scrolling through items."""
        total_time = 0.0
        
        for i in range(items):
            # Scroll speed varies
            scroll_delay = random.uniform(0.3, 1.5)
            await asyncio.sleep(scroll_delay)
            total_time += scroll_delay
            
            # Sometimes pause on an item
            if random.random() < 0.2:
                pause = random.uniform(1.0, 3.0)
                await asyncio.sleep(pause)
                total_time += pause
        
        return total_time
    
    def get_stats(self) -> dict:
        """Get network simulation stats."""
        avg_latency = (
            self._state.total_latency_ms / self._state.total_requests
            if self._state.total_requests > 0 else 0
        )
        
        return {
            "network_type": self._state.profile.value,
            "signal_strength": round(self._state.signal_strength, 2),
            "total_requests": self._state.total_requests,
            "avg_latency_ms": round(avg_latency, 1),
            "connection_drops": self._state.drops_count,
            "is_connected": self._state.is_connected,
            "session_duration_s": round(time.time() - self._session_start, 1),
        }
    
    @staticmethod
    def random_profile() -> NetworkProfile:
        """Get a random network profile with realistic distribution."""
        profiles = [
            (NetworkProfile.LTE_4G, 50),     # Most common
            (NetworkProfile.WIFI, 30),        # Common
            (NetworkProfile.MOBILE_5G, 10),   # Growing
            (NetworkProfile.MOBILE_3G, 8),    # Declining
            (NetworkProfile.ETHERNET, 2),     # Rare for mobile
        ]
        
        types, weights = zip(*profiles)
        return random.choices(types, weights=weights)[0]
