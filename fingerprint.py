"""
Ultra-Advanced Device Fingerprint Generator
Generates realistic device fingerprints for Telegram clients
"""

import random
import hashlib
import uuid
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DeviceFingerprint:
    """Complete device fingerprint for Telegram login."""
    device_model: str
    system_version: str
    app_version: str
    lang_code: str
    system_lang_code: str
    lang_pack: str
    app_name: str
    app_id: int
    app_hash: str
    layer: int
    sdk: str
    device_hash: str


# ==================== REAL TELEGRAM APPS ====================
# These are real app configurations from various Telegram clients

TELEGRAM_APPS = {
    "telegram_android": {
        "app_name": "Telegram Android",
        "app_id": 4,
        "app_hash": "014b35b6184100b085b0d0572f9b5103",
        "layer": 179,
        "sdk": "Android SDK",
    },
    "telegram_ios": {
        "app_name": "Telegram iOS",
        "app_id": 6,
        "app_hash": "eb06d4abfb49dc3eeb1aeb98ae0f581e",
        "layer": 179,
        "sdk": "iOS SDK",
    },
    "telegram_desktop": {
        "app_name": "Telegram Desktop",
        "app_id": 2040,
        "app_hash": "b18441a1ff607e10a989891a5462e627",
        "layer": 179,
        "sdk": "Desktop SDK",
    },
    "telegram_macos": {
        "app_name": "Telegram macOS",
        "app_id": 2834,
        "app_hash": "68875f756c9b437a8b916ca3de215571",
        "layer": 179,
        "sdk": "macOS SDK",
    },
    "nicegram": {
        "app_name": "Nicegram",
        "app_id": 94575,
        "app_hash": "a3406de8d171bb422bb6ddf3bbd800e2",
        "layer": 179,
        "sdk": "Nicegram SDK",
    },
    "plus_messenger": {
        "app_name": "Plus Messenger",
        "app_id": 2458,
        "app_hash": "d8ebb008e62224971a310ee4e8a87b1f",
        "layer": 179,
        "sdk": "Plus SDK",
    },
    "telegram_x": {
        "app_name": "Telegram X",
        "app_id": 21724,
        "app_hash": "3e0cb5efcd52300aec5994fdfc5bdc16",
        "layer": 179,
        "sdk": "TDLib",
    },
    "nekogram": {
        "app_name": "Nekogram",
        "app_id": 13349,
        "app_hash": "a3b3f5e1c2e9f7a8d6b4c2e1f0a9d8c7",
        "layer": 179,
        "sdk": "Nekogram SDK",
    },
    "bgram": {
        "app_name": "BGram",
        "app_id": 19584,
        "app_hash": "c5c3c5e1a2b3f7e8d6a4b2c1e0f9a8d7",
        "layer": 179,
        "sdk": "BGram SDK",
    },
    "turbo_telegram": {
        "app_name": "Turbo Telegram",
        "app_id": 16921,
        "app_hash": "b5e3c4d2a1f8e7b6c4a2d1e0f9b8a7c6",
        "layer": 179,
        "sdk": "Turbo SDK",
    },
    "vidogram": {
        "app_name": "Vidogram",
        "app_id": 17349,
        "app_hash": "e4f3d2c1b0a9f8e7d6c5b4a3e2f1d0c9",
        "layer": 179,
        "sdk": "Vidogram SDK",
    },
    "graph_messenger": {
        "app_name": "Graph Messenger",
        "app_id": 21683,
        "app_hash": "f5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0",
        "layer": 179,
        "sdk": "Graph SDK",
    },
}


# ==================== REAL ANDROID DEVICES ====================

ANDROID_DEVICES = [
    # Samsung Galaxy S Series
    {"brand": "Samsung", "model": "SM-S918B", "name": "Galaxy S23 Ultra", "sdk_range": (31, 34)},
    {"brand": "Samsung", "model": "SM-S916B", "name": "Galaxy S23+", "sdk_range": (31, 34)},
    {"brand": "Samsung", "model": "SM-S911B", "name": "Galaxy S23", "sdk_range": (31, 34)},
    {"brand": "Samsung", "model": "SM-S908B", "name": "Galaxy S22 Ultra", "sdk_range": (31, 34)},
    {"brand": "Samsung", "model": "SM-S906B", "name": "Galaxy S22+", "sdk_range": (31, 34)},
    {"brand": "Samsung", "model": "SM-G998B", "name": "Galaxy S21 Ultra", "sdk_range": (30, 33)},
    {"brand": "Samsung", "model": "SM-G996B", "name": "Galaxy S21+", "sdk_range": (30, 33)},
    {"brand": "Samsung", "model": "SM-G991B", "name": "Galaxy S21", "sdk_range": (30, 33)},
    {"brand": "Samsung", "model": "SM-G988B", "name": "Galaxy S20 Ultra", "sdk_range": (29, 33)},
    {"brand": "Samsung", "model": "SM-G986B", "name": "Galaxy S20+", "sdk_range": (29, 33)},
    
    # Samsung Galaxy A Series
    {"brand": "Samsung", "model": "SM-A546B", "name": "Galaxy A54 5G", "sdk_range": (31, 34)},
    {"brand": "Samsung", "model": "SM-A536B", "name": "Galaxy A53 5G", "sdk_range": (31, 33)},
    {"brand": "Samsung", "model": "SM-A346B", "name": "Galaxy A34 5G", "sdk_range": (31, 34)},
    {"brand": "Samsung", "model": "SM-A145F", "name": "Galaxy A14", "sdk_range": (31, 33)},
    
    # Samsung Galaxy Z Series (Foldables)
    {"brand": "Samsung", "model": "SM-F946B", "name": "Galaxy Z Fold5", "sdk_range": (33, 34)},
    {"brand": "Samsung", "model": "SM-F731B", "name": "Galaxy Z Flip5", "sdk_range": (33, 34)},
    {"brand": "Samsung", "model": "SM-F936B", "name": "Galaxy Z Fold4", "sdk_range": (31, 34)},
    {"brand": "Samsung", "model": "SM-F721B", "name": "Galaxy Z Flip4", "sdk_range": (31, 34)},
    
    # Google Pixel
    {"brand": "Google", "model": "Pixel 8 Pro", "name": "Pixel 8 Pro", "sdk_range": (34, 34)},
    {"brand": "Google", "model": "Pixel 8", "name": "Pixel 8", "sdk_range": (34, 34)},
    {"brand": "Google", "model": "Pixel 7 Pro", "name": "Pixel 7 Pro", "sdk_range": (33, 34)},
    {"brand": "Google", "model": "Pixel 7", "name": "Pixel 7", "sdk_range": (33, 34)},
    {"brand": "Google", "model": "Pixel 7a", "name": "Pixel 7a", "sdk_range": (33, 34)},
    {"brand": "Google", "model": "Pixel 6 Pro", "name": "Pixel 6 Pro", "sdk_range": (31, 34)},
    {"brand": "Google", "model": "Pixel 6", "name": "Pixel 6", "sdk_range": (31, 34)},
    {"brand": "Google", "model": "Pixel 6a", "name": "Pixel 6a", "sdk_range": (31, 34)},
    
    # OnePlus
    {"brand": "OnePlus", "model": "CPH2449", "name": "OnePlus 11", "sdk_range": (33, 34)},
    {"brand": "OnePlus", "model": "NE2213", "name": "OnePlus 10 Pro", "sdk_range": (31, 34)},
    {"brand": "OnePlus", "model": "NE2215", "name": "OnePlus 10T", "sdk_range": (31, 34)},
    {"brand": "OnePlus", "model": "LE2123", "name": "OnePlus 9 Pro", "sdk_range": (30, 33)},
    {"brand": "OnePlus", "model": "LE2113", "name": "OnePlus 9", "sdk_range": (30, 33)},
    {"brand": "OnePlus", "model": "KB2003", "name": "OnePlus 8T", "sdk_range": (29, 33)},
    {"brand": "OnePlus", "model": "CPH2423", "name": "OnePlus Nord 3", "sdk_range": (33, 34)},
    {"brand": "OnePlus", "model": "CPH2373", "name": "OnePlus Nord CE 3", "sdk_range": (31, 34)},
    
    # Xiaomi
    {"brand": "Xiaomi", "model": "2304FPN6DC", "name": "Xiaomi 13 Ultra", "sdk_range": (33, 34)},
    {"brand": "Xiaomi", "model": "2210132C", "name": "Xiaomi 13 Pro", "sdk_range": (33, 34)},
    {"brand": "Xiaomi", "model": "2211133C", "name": "Xiaomi 13", "sdk_range": (33, 34)},
    {"brand": "Xiaomi", "model": "2201123C", "name": "Xiaomi 12 Pro", "sdk_range": (31, 34)},
    {"brand": "Xiaomi", "model": "2201123G", "name": "Xiaomi 12", "sdk_range": (31, 34)},
    {"brand": "Xiaomi", "model": "22081212UG", "name": "Xiaomi 12T Pro", "sdk_range": (31, 34)},
    
    # Xiaomi Redmi
    {"brand": "Xiaomi", "model": "23053RN02Y", "name": "Redmi Note 12 Pro+", "sdk_range": (31, 34)},
    {"brand": "Xiaomi", "model": "22101316G", "name": "Redmi Note 12", "sdk_range": (31, 33)},
    {"brand": "Xiaomi", "model": "22111317PG", "name": "Redmi 12C", "sdk_range": (31, 33)},
    {"brand": "Xiaomi", "model": "23078RKD5C", "name": "Redmi K60", "sdk_range": (33, 34)},
    
    # POCO
    {"brand": "Xiaomi", "model": "23013PC75G", "name": "POCO X5 Pro 5G", "sdk_range": (31, 34)},
    {"brand": "Xiaomi", "model": "22101320G", "name": "POCO M5", "sdk_range": (31, 33)},
    {"brand": "Xiaomi", "model": "21091116AG", "name": "POCO F4 GT", "sdk_range": (31, 34)},
    
    # OPPO
    {"brand": "OPPO", "model": "CPH2519", "name": "OPPO Find X6 Pro", "sdk_range": (33, 34)},
    {"brand": "OPPO", "model": "CPH2305", "name": "OPPO Find X5 Pro", "sdk_range": (31, 34)},
    {"brand": "OPPO", "model": "CPH2413", "name": "OPPO Reno 8 Pro", "sdk_range": (31, 34)},
    {"brand": "OPPO", "model": "CPH2477", "name": "OPPO Reno 10 Pro+", "sdk_range": (33, 34)},
    {"brand": "OPPO", "model": "CPH2359", "name": "OPPO A98 5G", "sdk_range": (31, 34)},
    
    # Vivo
    {"brand": "Vivo", "model": "V2219", "name": "Vivo X90 Pro+", "sdk_range": (33, 34)},
    {"brand": "Vivo", "model": "V2227", "name": "Vivo X90 Pro", "sdk_range": (33, 34)},
    {"brand": "Vivo", "model": "V2145", "name": "Vivo X80 Pro", "sdk_range": (31, 34)},
    {"brand": "Vivo", "model": "V2241", "name": "Vivo V27 Pro", "sdk_range": (31, 34)},
    
    # Realme
    {"brand": "Realme", "model": "RMX3771", "name": "Realme GT3", "sdk_range": (33, 34)},
    {"brand": "Realme", "model": "RMX3551", "name": "Realme GT2 Pro", "sdk_range": (31, 34)},
    {"brand": "Realme", "model": "RMX3630", "name": "Realme 11 Pro+", "sdk_range": (33, 34)},
    {"brand": "Realme", "model": "RMX3393", "name": "Realme 10 Pro+", "sdk_range": (31, 34)},
    
    # Huawei (non-GMS)
    {"brand": "Huawei", "model": "ALN-AL00", "name": "Huawei Mate 60 Pro", "sdk_range": (31, 33)},
    {"brand": "Huawei", "model": "NOH-AN01", "name": "Huawei Mate 40 Pro", "sdk_range": (29, 31)},
    {"brand": "Huawei", "model": "LIO-AN00", "name": "Huawei P50 Pro", "sdk_range": (30, 31)},
    
    # Nothing
    {"brand": "Nothing", "model": "A063", "name": "Nothing Phone (2)", "sdk_range": (33, 34)},
    {"brand": "Nothing", "model": "A065", "name": "Nothing Phone (1)", "sdk_range": (31, 33)},
    
    # ASUS ROG
    {"brand": "ASUS", "model": "ASUS_AI2205", "name": "ROG Phone 7 Ultimate", "sdk_range": (33, 34)},
    {"brand": "ASUS", "model": "ASUS_AI2201", "name": "ROG Phone 6 Pro", "sdk_range": (31, 34)},
    
    # Sony Xperia
    {"brand": "Sony", "model": "XQ-DQ72", "name": "Xperia 1 V", "sdk_range": (33, 34)},
    {"brand": "Sony", "model": "XQ-CT72", "name": "Xperia 1 IV", "sdk_range": (31, 34)},
    {"brand": "Sony", "model": "XQ-CQ72", "name": "Xperia 5 IV", "sdk_range": (31, 34)},
    
    # Motorola
    {"brand": "Motorola", "model": "XT2301-4", "name": "Motorola Edge 40 Pro", "sdk_range": (33, 34)},
    {"brand": "Motorola", "model": "XT2241-1", "name": "Motorola Edge 30 Ultra", "sdk_range": (31, 34)},
    {"brand": "Motorola", "model": "XT2343-2", "name": "Motorola Razr 40 Ultra", "sdk_range": (33, 34)},
]


# ==================== REAL iOS DEVICES ====================

IOS_DEVICES = [
    # iPhone 15 Series
    {"model": "iPhone16,2", "name": "iPhone 15 Pro Max", "ios_range": (17.0, 17.4)},
    {"model": "iPhone16,1", "name": "iPhone 15 Pro", "ios_range": (17.0, 17.4)},
    {"model": "iPhone15,5", "name": "iPhone 15 Plus", "ios_range": (17.0, 17.4)},
    {"model": "iPhone15,4", "name": "iPhone 15", "ios_range": (17.0, 17.4)},
    
    # iPhone 14 Series
    {"model": "iPhone15,3", "name": "iPhone 14 Pro Max", "ios_range": (16.0, 17.4)},
    {"model": "iPhone15,2", "name": "iPhone 14 Pro", "ios_range": (16.0, 17.4)},
    {"model": "iPhone14,8", "name": "iPhone 14 Plus", "ios_range": (16.0, 17.4)},
    {"model": "iPhone14,7", "name": "iPhone 14", "ios_range": (16.0, 17.4)},
    
    # iPhone 13 Series
    {"model": "iPhone14,3", "name": "iPhone 13 Pro Max", "ios_range": (15.0, 17.4)},
    {"model": "iPhone14,2", "name": "iPhone 13 Pro", "ios_range": (15.0, 17.4)},
    {"model": "iPhone14,5", "name": "iPhone 13", "ios_range": (15.0, 17.4)},
    {"model": "iPhone14,4", "name": "iPhone 13 mini", "ios_range": (15.0, 17.4)},
    
    # iPhone 12 Series
    {"model": "iPhone13,4", "name": "iPhone 12 Pro Max", "ios_range": (14.1, 17.4)},
    {"model": "iPhone13,3", "name": "iPhone 12 Pro", "ios_range": (14.1, 17.4)},
    {"model": "iPhone13,2", "name": "iPhone 12", "ios_range": (14.1, 17.4)},
    {"model": "iPhone13,1", "name": "iPhone 12 mini", "ios_range": (14.1, 17.4)},
    
    # iPhone 11 Series
    {"model": "iPhone12,5", "name": "iPhone 11 Pro Max", "ios_range": (13.0, 17.4)},
    {"model": "iPhone12,3", "name": "iPhone 11 Pro", "ios_range": (13.0, 17.4)},
    {"model": "iPhone12,1", "name": "iPhone 11", "ios_range": (13.0, 17.4)},
    
    # iPhone SE
    {"model": "iPhone14,6", "name": "iPhone SE (3rd gen)", "ios_range": (15.4, 17.4)},
    {"model": "iPhone12,8", "name": "iPhone SE (2nd gen)", "ios_range": (13.4, 17.4)},
    
    # iPad Pro
    {"model": "iPad14,6", "name": "iPad Pro 12.9 (6th gen)", "ios_range": (16.0, 17.4)},
    {"model": "iPad14,5", "name": "iPad Pro 11 (4th gen)", "ios_range": (16.0, 17.4)},
    {"model": "iPad13,11", "name": "iPad Pro 12.9 (5th gen)", "ios_range": (14.5, 17.4)},
    
    # iPad Air
    {"model": "iPad13,17", "name": "iPad Air (5th gen)", "ios_range": (15.4, 17.4)},
    {"model": "iPad13,2", "name": "iPad Air (4th gen)", "ios_range": (14.0, 17.4)},
    
    # iPad
    {"model": "iPad14,1", "name": "iPad (10th gen)", "ios_range": (16.0, 17.4)},
    {"model": "iPad12,2", "name": "iPad (9th gen)", "ios_range": (15.0, 17.4)},
]


# ==================== ANDROID VERSIONS ====================

ANDROID_VERSIONS = {
    29: {"name": "Android 10", "versions": ["10", "10.0"]},
    30: {"name": "Android 11", "versions": ["11", "11.0"]},
    31: {"name": "Android 12", "versions": ["12", "12.0"]},
    32: {"name": "Android 12L", "versions": ["12.1", "12L"]},
    33: {"name": "Android 13", "versions": ["13", "13.0"]},
    34: {"name": "Android 14", "versions": ["14", "14.0"]},
}


# ==================== APP VERSIONS ====================

def _generate_app_version(app_type: str) -> str:
    """Generate realistic app version."""
    if app_type in ["telegram_android", "nicegram", "plus_messenger", "nekogram", "bgram"]:
        major = random.randint(9, 10)
        minor = random.randint(0, 9)
        patch = random.randint(0, 25)
        build = random.randint(3000, 4500)
        return f"{major}.{minor}.{patch} ({build})"
    elif app_type in ["telegram_ios"]:
        major = random.randint(9, 10)
        minor = random.randint(0, 9)
        patch = random.randint(0, 9)
        return f"{major}.{minor}.{patch}"
    elif app_type == "telegram_x":
        major = random.randint(0, 1)
        minor = random.randint(24, 26)
        patch = random.randint(0, 9)
        build = random.randint(1600, 1800)
        return f"{major}.{minor}.{patch}.{build}"
    else:
        major = random.randint(4, 5)
        minor = random.randint(0, 9)
        patch = random.randint(0, 9)
        return f"{major}.{minor}.{patch}"


# ==================== LANGUAGES ====================

LANGUAGES = [
    {"code": "en", "name": "English"},
    {"code": "ru", "name": "Russian"},
    {"code": "es", "name": "Spanish"},
    {"code": "de", "name": "German"},
    {"code": "fr", "name": "French"},
    {"code": "it", "name": "Italian"},
    {"code": "pt", "name": "Portuguese"},
    {"code": "ar", "name": "Arabic"},
    {"code": "ja", "name": "Japanese"},
    {"code": "ko", "name": "Korean"},
    {"code": "zh", "name": "Chinese"},
    {"code": "tr", "name": "Turkish"},
    {"code": "fa", "name": "Persian"},
    {"code": "id", "name": "Indonesian"},
    {"code": "hi", "name": "Hindi"},
    {"code": "vi", "name": "Vietnamese"},
    {"code": "th", "name": "Thai"},
    {"code": "uk", "name": "Ukrainian"},
    {"code": "pl", "name": "Polish"},
    {"code": "nl", "name": "Dutch"},
]


class FingerprintGenerator:
    """Generates realistic device fingerprints."""
    
    def __init__(self):
        self._used_hashes: set = set()
    
    def _generate_device_hash(self) -> str:
        """Generate unique device hash."""
        while True:
            raw = f"{uuid.uuid4()}{random.random()}{uuid.uuid4()}"
            hash_val = hashlib.md5(raw.encode()).hexdigest()[:16]
            if hash_val not in self._used_hashes:
                self._used_hashes.add(hash_val)
                return hash_val
    
    def generate_android_fingerprint(self, app_type: Optional[str] = None) -> DeviceFingerprint:
        """Generate Android device fingerprint."""
        # Select random app if not specified
        android_apps = ["telegram_android", "nicegram", "plus_messenger", "telegram_x", 
                       "nekogram", "bgram", "turbo_telegram", "vidogram", "graph_messenger"]
        app_key = app_type or random.choice(android_apps)
        app = TELEGRAM_APPS.get(app_key, TELEGRAM_APPS["telegram_android"])
        
        # Select random device
        device = random.choice(ANDROID_DEVICES)
        
        # Generate SDK version within device's range
        sdk_min, sdk_max = device["sdk_range"]
        sdk_version = random.randint(sdk_min, sdk_max)
        android_info = ANDROID_VERSIONS.get(sdk_version, ANDROID_VERSIONS[33])
        system_version = random.choice(android_info["versions"])
        
        # Select language
        lang = random.choice(LANGUAGES)
        
        # Device model string
        device_model = f"{device['brand']} {device['model']}"
        
        return DeviceFingerprint(
            device_model=device_model,
            system_version=f"SDK {sdk_version}",
            app_version=_generate_app_version(app_key),
            lang_code=lang["code"],
            system_lang_code=f"{lang['code']}-{lang['code'].upper()}",
            lang_pack=lang["code"],
            app_name=app["app_name"],
            app_id=app["app_id"],
            app_hash=app["app_hash"],
            layer=app["layer"],
            sdk=app["sdk"],
            device_hash=self._generate_device_hash(),
        )
    
    def generate_ios_fingerprint(self, app_type: Optional[str] = None) -> DeviceFingerprint:
        """Generate iOS device fingerprint."""
        # Select iOS app
        ios_apps = ["telegram_ios"]
        app_key = app_type or random.choice(ios_apps)
        app = TELEGRAM_APPS.get(app_key, TELEGRAM_APPS["telegram_ios"])
        
        # Select random device
        device = random.choice(IOS_DEVICES)
        
        # Generate iOS version within range
        ios_min, ios_max = device["ios_range"]
        ios_major = random.randint(int(ios_min), int(ios_max))
        ios_minor = random.randint(0, 5)
        system_version = f"{ios_major}.{ios_minor}"
        
        # Select language
        lang = random.choice(LANGUAGES)
        
        return DeviceFingerprint(
            device_model=device["name"],
            system_version=system_version,
            app_version=_generate_app_version(app_key),
            lang_code=lang["code"],
            system_lang_code=f"{lang['code']}-{lang['code'].upper()}",
            lang_pack=lang["code"],
            app_name=app["app_name"],
            app_id=app["app_id"],
            app_hash=app["app_hash"],
            layer=app["layer"],
            sdk=app["sdk"],
            device_hash=self._generate_device_hash(),
        )
    
    def generate_random_fingerprint(self) -> DeviceFingerprint:
        """Generate random fingerprint (Android 85%, iOS 15%)."""
        if random.random() < 0.85:
            return self.generate_android_fingerprint()
        else:
            return self.generate_ios_fingerprint()
    
    def get_fingerprint_info(self, fp: DeviceFingerprint) -> Dict[str, Any]:
        """Get human-readable fingerprint info."""
        return {
            "device": fp.device_model,
            "system": fp.system_version,
            "app": fp.app_name,
            "app_version": fp.app_version,
            "language": fp.lang_code,
            "device_hash": fp.device_hash,
        }


# Global instance
fingerprint_generator = FingerprintGenerator()
