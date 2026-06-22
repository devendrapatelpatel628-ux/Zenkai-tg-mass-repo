"""
Stealth Proxy System v2
Advanced proxy management with quality scoring, geo-matching,
reputation tracking, and intelligent rotation.
"""

import asyncio
import aiohttp
import time
import json
import re
import random
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import socks


class ProxyType(Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"
    MTPROTO = "mtproto"


class ProxyQuality(Enum):
    """Proxy quality classification."""
    RESIDENTIAL = "residential"    # Best: real ISP IPs
    MOBILE = "mobile"              # Great: mobile carrier IPs
    ISP = "isp"                    # Good: static ISP IPs
    DATACENTER = "datacenter"      # OK: cloud/hosting IPs
    UNKNOWN = "unknown"            # Unclassified


class ProxyState(Enum):
    """Proxy lifecycle state."""
    FRESH = "fresh"                # Just added, not validated
    VALIDATED = "validated"        # Tested and working
    ASSIGNED = "assigned"          # Reserved for a phone
    USED = "used"                  # Used once, done forever
    DEAD = "dead"                  # Failed validation or usage
    BLACKLISTED = "blacklisted"   # Known bad proxy


@dataclass
class Proxy:
    """Enhanced proxy with quality scoring and reputation."""
    host: str
    port: int
    proxy_type: ProxyType
    username: Optional[str] = None
    password: Optional[str] = None
    secret: Optional[str] = None
    
    # Identity
    id: str = field(default_factory=lambda: f"px_{hashlib.md5(f'{time.time()}{random.random()}'.encode()).hexdigest()[:10]}")
    added_at: float = field(default_factory=time.time)
    
    # State
    state: ProxyState = ProxyState.FRESH
    
    # Quality & reputation
    quality: ProxyQuality = ProxyQuality.UNKNOWN
    quality_score: float = 50.0  # 0-100
    
    # Validation results
    validated: bool = False
    validation_time: Optional[float] = None
    latency_ms: Optional[int] = None
    country: Optional[str] = None
    city: Optional[str] = None
    isp: Optional[str] = None
    ip_address: Optional[str] = None
    is_anonymous: bool = True
    
    # Usage tracking
    used: bool = False
    used_at: Optional[float] = None
    used_for_phone: Optional[str] = None
    usage_result: Optional[str] = None  # success, failed, flood_wait
    
    # Failure tracking
    failure_count: int = 0
    last_failure: Optional[float] = None
    failure_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "host": self.host,
            "port": self.port,
            "type": self.proxy_type.value,
            "username": self.username,
            "password": self.password,
            "secret": self.secret,
            "state": self.state.value,
            "quality": self.quality.value,
            "quality_score": round(self.quality_score, 1),
            "validated": self.validated,
            "latency_ms": self.latency_ms,
            "country": self.country,
            "city": self.city,
            "isp": self.isp,
            "is_anonymous": self.is_anonymous,
            "used": self.used,
            "used_for_phone": self.used_for_phone,
            "usage_result": self.usage_result,
        }
    
    def to_telethon_proxy(self) -> Optional[Tuple]:
        """Convert to Telethon proxy format."""
        if self.proxy_type == ProxyType.SOCKS5:
            return (socks.SOCKS5, self.host, self.port, True, self.username, self.password)
        elif self.proxy_type == ProxyType.SOCKS4:
            return (socks.SOCKS4, self.host, self.port, True, self.username, self.password)
        elif self.proxy_type in [ProxyType.HTTP, ProxyType.HTTPS]:
            return (socks.HTTP, self.host, self.port, True, self.username, self.password)
        return None
    
    def to_mtproto_dict(self) -> Optional[Dict[str, Any]]:
        if self.proxy_type == ProxyType.MTPROTO:
            return {'proxy_type': 'mtproto', 'addr': self.host, 'port': self.port, 'secret': self.secret}
        return None
    
    @classmethod
    def from_string(cls, proxy_str: str) -> Optional['Proxy']:
        """Parse proxy from various string formats."""
        proxy_str = proxy_str.strip()
        if not proxy_str or proxy_str.startswith('#'):
            return None
        
        proxy_type = ProxyType.SOCKS5
        username = None
        password = None
        
        # Protocol prefix
        protocol_match = re.match(r'^(https?|socks[45]?|mtproto)://', proxy_str.lower())
        if protocol_match:
            protocol = protocol_match.group(1).lower()
            type_map = {
                "http": ProxyType.HTTP, "https": ProxyType.HTTPS,
                "socks4": ProxyType.SOCKS4, "socks5": ProxyType.SOCKS5,
                "socks": ProxyType.SOCKS5, "mtproto": ProxyType.MTPROTO,
            }
            proxy_type = type_map.get(protocol, ProxyType.SOCKS5)
            proxy_str = proxy_str[len(protocol_match.group(0)):]
        
        # user:pass@
        auth_match = re.match(r'^([^:]+):([^@]+)@', proxy_str)
        if auth_match:
            username = auth_match.group(1)
            password = auth_match.group(2)
            proxy_str = proxy_str[len(auth_match.group(0)):]
        
        # host:port[:user:pass]
        parts = proxy_str.split(':')
        if len(parts) < 2:
            return None
        
        host = parts[0]
        try:
            port = int(parts[1])
        except ValueError:
            return None
        
        if len(parts) >= 4 and not username:
            username = parts[2]
            password = parts[3]
        
        return cls(host=host, port=port, proxy_type=proxy_type, username=username, password=password)


# Known datacenter ASN ranges (simplified)
DATACENTER_KEYWORDS = [
    'amazon', 'aws', 'google', 'microsoft', 'azure', 'digitalocean',
    'linode', 'vultr', 'ovh', 'hetzner', 'contabo', 'hostinger',
    'cloudflare', 'oracle', 'alibaba', 'tencent', 'hosting', 'server',
    'datacenter', 'data center', 'colocation', 'vps', 'cloud',
]

MOBILE_KEYWORDS = [
    'mobile', 'wireless', 'cellular', 'cell', 'lte', '4g', '5g',
    't-mobile', 'at&t', 'verizon', 'vodafone', 'orange', 'telefonica',
    'airtel', 'mtn', 'jio', 'etisalat',
]

RESIDENTIAL_KEYWORDS = [
    'residential', 'broadband', 'cable', 'dsl', 'fiber', 'fibre',
    'comcast', 'spectrum', 'cox', 'xfinity', 'sky', 'bt',
]


def classify_proxy_quality(isp: Optional[str]) -> ProxyQuality:
    """Classify proxy quality based on ISP name."""
    if not isp:
        return ProxyQuality.UNKNOWN
    
    isp_lower = isp.lower()
    
    if any(kw in isp_lower for kw in MOBILE_KEYWORDS):
        return ProxyQuality.MOBILE
    if any(kw in isp_lower for kw in RESIDENTIAL_KEYWORDS):
        return ProxyQuality.RESIDENTIAL
    if any(kw in isp_lower for kw in DATACENTER_KEYWORDS):
        return ProxyQuality.DATACENTER
    
    return ProxyQuality.ISP


# Quality scores by classification
QUALITY_SCORES = {
    ProxyQuality.RESIDENTIAL: 95,
    ProxyQuality.MOBILE: 90,
    ProxyQuality.ISP: 70,
    ProxyQuality.DATACENTER: 40,
    ProxyQuality.UNKNOWN: 50,
}


class ProxyManager:
    """
    Stealth Proxy System v2 with:
    - Quality scoring (residential > datacenter)
    - Geographic matching (proxy country ↔ phone country)
    - One-time use (never reused)
    - Reputation tracking
    - Smart selection (best proxy for the job)
    - No retry on same proxy ever
    - Auto dead proxy removal
    """
    
    PROXY_FILE = Path("./data/proxies.json")
    VALIDATION_TIMEOUT = 12
    TEST_URLS = [
        "http://ip-api.com/json",
        "https://api.ipify.org?format=json",
        "http://httpbin.org/ip",
    ]
    
    def __init__(self):
        self._proxies: Dict[str, Proxy] = {}
        self._available_queue: List[str] = []  # Sorted by quality
        self._dead_proxies: set = set()
        self._used_proxies: Dict[str, str] = {}  # phone -> proxy_id
        self._country_map: Dict[str, List[str]] = defaultdict(list)  # country -> proxy_ids
        self._lock = asyncio.Lock()
        self._usage_history: List[Dict[str, Any]] = []
        
        self._load_proxies()
    
    def _load_proxies(self):
        """Load proxies from file."""
        if self.PROXY_FILE.exists():
            try:
                with open(self.PROXY_FILE, 'r') as f:
                    data = json.load(f)
                    for p_data in data.get("proxies", []):
                        proxy = Proxy(
                            host=p_data["host"],
                            port=p_data["port"],
                            proxy_type=ProxyType(p_data["type"]),
                            username=p_data.get("username"),
                            password=p_data.get("password"),
                            secret=p_data.get("secret"),
                            id=p_data["id"],
                            state=ProxyState(p_data.get("state", "fresh")),
                            quality=ProxyQuality(p_data.get("quality", "unknown")),
                            quality_score=p_data.get("quality_score", 50),
                            validated=p_data.get("validated", False),
                            latency_ms=p_data.get("latency_ms"),
                            country=p_data.get("country"),
                            city=p_data.get("city"),
                            isp=p_data.get("isp"),
                            used=p_data.get("used", False),
                        )
                        self._proxies[proxy.id] = proxy
                        
                        if proxy.state == ProxyState.VALIDATED:
                            self._available_queue.append(proxy.id)
                            if proxy.country:
                                self._country_map[proxy.country.upper()].append(proxy.id)
                        elif proxy.state == ProxyState.DEAD:
                            self._dead_proxies.add(proxy.id)
                
                # Sort queue by quality score (best first)
                self._sort_queue()
            except Exception as e:
                print(f"Error loading proxies: {e}")
    
    def _save_proxies(self):
        """Save proxies to file."""
        self.PROXY_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {
                "proxies": [p.to_dict() for p in self._proxies.values()],
                "stats": self.get_stats(),
                "updated_at": time.time(),
            }
            with open(self.PROXY_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving proxies: {e}")
    
    def _sort_queue(self):
        """Sort available queue by quality score (best first)."""
        self._available_queue.sort(
            key=lambda pid: self._proxies[pid].quality_score if pid in self._proxies else 0,
            reverse=True
        )
    
    # ==================== Validation ====================
    
    async def _validate_proxy(self, proxy: Proxy) -> Tuple[bool, Optional[int], Optional[Dict]]:
        """
        Validate proxy and gather intelligence.
        Returns: (is_valid, latency_ms, geo_info)
        """
        if proxy.proxy_type == ProxyType.MTPROTO:
            return (True, None, None)
        
        proxy_url = self._get_proxy_url(proxy)
        
        for test_url in self.TEST_URLS:
            try:
                start = time.time()
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        test_url,
                        proxy=proxy_url,
                        timeout=aiohttp.ClientTimeout(total=self.VALIDATION_TIMEOUT),
                        ssl=False,
                    ) as response:
                        if response.status == 200:
                            latency = int((time.time() - start) * 1000)
                            data = await response.json()
                            
                            geo_info = {
                                "ip": data.get("query") or data.get("ip") or data.get("origin"),
                                "country": data.get("country") or data.get("countryCode"),
                                "city": data.get("city"),
                                "isp": data.get("isp") or data.get("org"),
                                "as": data.get("as"),
                            }
                            return (True, latency, geo_info)
            except Exception:
                continue
        
        return (False, None, None)
    
    def _get_proxy_url(self, proxy: Proxy) -> str:
        auth = f"{proxy.username}:{proxy.password}@" if proxy.username and proxy.password else ""
        scheme = proxy.proxy_type.value
        return f"{scheme}://{auth}{proxy.host}:{proxy.port}"
    
    # ==================== Add Proxies ====================
    
    async def add_proxy(self, proxy: Proxy, validate: bool = True) -> Dict[str, Any]:
        """Add a single proxy with quality classification."""
        async with self._lock:
            # Duplicate check
            for existing in self._proxies.values():
                if existing.host == proxy.host and existing.port == proxy.port:
                    return {"success": False, "error": "Proxy already exists"}
            
            if validate:
                is_valid, latency, geo_info = await self._validate_proxy(proxy)
                if not is_valid:
                    return {"success": False, "error": "Proxy validation failed"}
                
                proxy.validated = True
                proxy.validation_time = time.time()
                proxy.latency_ms = latency
                proxy.state = ProxyState.VALIDATED
                
                if geo_info:
                    proxy.country = geo_info.get("country")
                    proxy.city = geo_info.get("city")
                    proxy.isp = geo_info.get("isp")
                    proxy.ip_address = geo_info.get("ip")
                    
                    # Classify quality
                    proxy.quality = classify_proxy_quality(proxy.isp)
                    proxy.quality_score = QUALITY_SCORES.get(proxy.quality, 50)
                    
                    # Latency adjustment
                    if latency and latency < 200:
                        proxy.quality_score += 5
                    elif latency and latency > 1000:
                        proxy.quality_score -= 10
                    
                    # Country index
                    if proxy.country:
                        self._country_map[proxy.country.upper()].append(proxy.id)
            else:
                proxy.state = ProxyState.VALIDATED  # Trust without validation
            
            self._proxies[proxy.id] = proxy
            self._available_queue.append(proxy.id)
            self._sort_queue()
            self._save_proxies()
            
            quality_str = f" | Quality: {proxy.quality.value} ({proxy.quality_score:.0f})" if proxy.quality != ProxyQuality.UNKNOWN else ""
            country_str = f" | {proxy.country}" if proxy.country else ""
            print(f"   ✅ Added: {proxy.host}:{proxy.port}{country_str}{quality_str}")
            
            return {"success": True, "proxy": proxy.to_dict()}
    
    async def add_proxies_bulk(self, proxy_strings: List[str], validate: bool = True) -> Dict[str, Any]:
        """Add multiple proxies from string list."""
        results = {"added": 0, "failed": 0, "duplicates": 0, "errors": []}
        
        for proxy_str in proxy_strings:
            proxy = Proxy.from_string(proxy_str)
            if not proxy:
                results["failed"] += 1
                results["errors"].append(f"Invalid format: {proxy_str[:50]}")
                continue
            
            result = await self.add_proxy(proxy, validate=validate)
            if result["success"]:
                results["added"] += 1
            elif "already exists" in result.get("error", ""):
                results["duplicates"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"{proxy_str[:30]}: {result.get('error')}")
        
        return results
    
    # ==================== Smart Selection ====================
    
    async def get_proxy_for_login(
        self,
        phone: str,
        preferred_country: Optional[str] = None,
    ) -> Optional[Proxy]:
        """
        Get the best unused proxy for login.
        - Quality-sorted selection (residential first)
        - Optional geographic matching
        - One-time use only
        - No retry on failed proxies
        """
        async with self._lock:
            # Already assigned?
            if phone in self._used_proxies:
                pid = self._used_proxies[phone]
                if pid in self._proxies and self._proxies[pid].state == ProxyState.ASSIGNED:
                    return self._proxies[pid]
            
            # Try country-matched proxy first
            if preferred_country:
                country_key = preferred_country.upper()
                country_proxies = self._country_map.get(country_key, [])
                for pid in country_proxies:
                    if pid in self._available_queue and pid in self._proxies:
                        proxy = self._proxies[pid]
                        if proxy.state == ProxyState.VALIDATED and not proxy.used:
                            return await self._assign_proxy(proxy, phone)
            
            # Quality-sorted selection
            while self._available_queue:
                pid = self._available_queue.pop(0)
                
                if pid in self._dead_proxies or pid not in self._proxies:
                    continue
                
                proxy = self._proxies[pid]
                if proxy.used or proxy.state not in [ProxyState.VALIDATED, ProxyState.FRESH]:
                    continue
                
                # Quick re-validation
                is_valid, latency, _ = await self._validate_proxy(proxy)
                if not is_valid:
                    proxy.state = ProxyState.DEAD
                    self._dead_proxies.add(pid)
                    proxy.failure_count += 1
                    proxy.last_failure = time.time()
                    proxy.failure_reason = "re-validation failed"
                    print(f"   ⚠️ Proxy dead: {proxy.host}:{proxy.port}")
                    continue
                
                if latency:
                    proxy.latency_ms = latency
                
                return await self._assign_proxy(proxy, phone)
            
            return None
    
    async def _assign_proxy(self, proxy: Proxy, phone: str) -> Proxy:
        """Assign proxy to a phone number (one-time use)."""
        proxy.state = ProxyState.ASSIGNED
        proxy.used = True
        proxy.used_at = time.time()
        proxy.used_for_phone = phone
        self._used_proxies[phone] = proxy.id
        
        # Remove from country map
        if proxy.country:
            country_key = proxy.country.upper()
            if proxy.id in self._country_map.get(country_key, []):
                self._country_map[country_key].remove(proxy.id)
        
        self._save_proxies()
        
        quality_tag = f" [{proxy.quality.value}]" if proxy.quality != ProxyQuality.UNKNOWN else ""
        country_tag = f" ({proxy.country})" if proxy.country else ""
        print(f"   🔗 Assigned {proxy.host}:{proxy.port}{country_tag}{quality_tag} → {phone}")
        
        return proxy
    
    # ==================== Usage Recording ====================
    
    async def record_proxy_result(
        self,
        phone: str,
        success: bool,
        error: Optional[str] = None,
    ):
        """Record the result of a proxy usage."""
        async with self._lock:
            pid = self._used_proxies.get(phone)
            if not pid or pid not in self._proxies:
                return
            
            proxy = self._proxies[pid]
            proxy.state = ProxyState.USED
            proxy.usage_result = "success" if success else f"failed: {error or 'unknown'}"
            
            if not success:
                proxy.failure_count += 1
                proxy.last_failure = time.time()
                proxy.failure_reason = error
            
            self._usage_history.append({
                "proxy_id": pid,
                "phone": phone,
                "success": success,
                "error": error,
                "quality": proxy.quality.value,
                "country": proxy.country,
                "latency_ms": proxy.latency_ms,
                "timestamp": time.time(),
            })
            
            self._save_proxies()
    
    async def mark_proxy_dead(self, proxy_id: str):
        async with self._lock:
            self._dead_proxies.add(proxy_id)
            if proxy_id in self._proxies:
                self._proxies[proxy_id].state = ProxyState.DEAD
            if proxy_id in self._available_queue:
                self._available_queue.remove(proxy_id)
            self._save_proxies()
    
    async def release_proxy(self, phone: str, mark_dead: bool = False):
        async with self._lock:
            if phone in self._used_proxies:
                pid = self._used_proxies[phone]
                if mark_dead and pid in self._proxies:
                    self._proxies[pid].state = ProxyState.DEAD
                    self._dead_proxies.add(pid)
                del self._used_proxies[phone]
                self._save_proxies()
    
    # ==================== Cleanup ====================
    
    async def remove_used_proxies(self):
        async with self._lock:
            to_remove = [pid for pid, p in self._proxies.items() if p.state == ProxyState.USED]
            for pid in to_remove:
                del self._proxies[pid]
            self._save_proxies()
            return len(to_remove)
    
    async def remove_dead_proxies(self):
        async with self._lock:
            to_remove = [pid for pid, p in self._proxies.items() if p.state == ProxyState.DEAD]
            for pid in to_remove:
                del self._proxies[pid]
            self._dead_proxies.clear()
            self._save_proxies()
            return len(to_remove)
    
    async def clear_all_proxies(self):
        async with self._lock:
            self._proxies.clear()
            self._available_queue.clear()
            self._dead_proxies.clear()
            self._used_proxies.clear()
            self._country_map.clear()
            self._save_proxies()
    
    # ==================== Analytics ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Enhanced proxy statistics."""
        proxies = list(self._proxies.values())
        
        state_counts = defaultdict(int)
        quality_counts = defaultdict(int)
        country_counts = defaultdict(int)
        
        latencies = []
        
        for p in proxies:
            state_counts[p.state.value] += 1
            quality_counts[p.quality.value] += 1
            if p.country:
                country_counts[p.country] += 1
            if p.latency_ms:
                latencies.append(p.latency_ms)
        
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        # Usage analytics
        total_used = len(self._usage_history)
        successful = len([u for u in self._usage_history if u.get("success")])
        
        return {
            "total": len(proxies),
            "available": len(self._available_queue),
            "validated": state_counts.get("validated", 0),
            "used": state_counts.get("used", 0),
            "dead": state_counts.get("dead", 0) + len(self._dead_proxies),
            "assigned": state_counts.get("assigned", 0),
            "quality": dict(quality_counts),
            "countries": dict(sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "avg_latency_ms": round(avg_latency, 1),
            "usage_success_rate": round((successful / total_used * 100), 1) if total_used > 0 else 0,
            "total_usages": total_used,
        }
    
    def get_all_proxies(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._proxies.values()]
    
    def get_quality_breakdown(self) -> Dict[str, Any]:
        """Get detailed quality analysis."""
        proxies = list(self._proxies.values())
        
        breakdown = {}
        for quality in ProxyQuality:
            q_proxies = [p for p in proxies if p.quality == quality]
            if q_proxies:
                breakdown[quality.value] = {
                    "count": len(q_proxies),
                    "available": len([p for p in q_proxies if p.state == ProxyState.VALIDATED]),
                    "avg_latency": round(
                        sum(p.latency_ms or 0 for p in q_proxies) / len(q_proxies), 1
                    ),
                    "countries": list(set(p.country for p in q_proxies if p.country)),
                }
        
        return breakdown
    
    def get_geographic_coverage(self) -> Dict[str, int]:
        """Get proxy counts by country."""
        coverage = defaultdict(int)
        for p in self._proxies.values():
            if p.country and p.state in [ProxyState.VALIDATED, ProxyState.FRESH]:
                coverage[p.country] += 1
        return dict(sorted(coverage.items(), key=lambda x: x[1], reverse=True))


# Global instance
proxy_manager = ProxyManager()
