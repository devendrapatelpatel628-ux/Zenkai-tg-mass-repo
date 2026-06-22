"""
Account Warmup System
New accounts need to be "warmed up" before heavy usage to avoid bans.
Simulates natural human behavior over time.
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

from telethon import TelegramClient
from telethon.tl.functions.messages import (
    GetDialogsRequest,
    ReadHistoryRequest,
    SetTypingRequest,
)
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.contacts import GetContactsRequest
from telethon.tl.types import SendMessageTypingAction, InputPeerEmpty


class WarmupStage(Enum):
    """Warmup progression stages."""
    NEW = "new"                    # Just created, very limited
    BEGINNING = "beginning"        # Day 1-3, light activity
    DEVELOPING = "developing"      # Day 4-7, moderate activity
    ESTABLISHED = "established"    # Day 8-14, normal activity
    MATURE = "mature"              # Day 15+, full capability
    TRUSTED = "trusted"            # Day 30+, high trust


@dataclass
class WarmupProfile:
    """Account warmup profile and progress."""
    account_id: str
    phone: str
    stage: WarmupStage = WarmupStage.NEW
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    last_activity: Optional[float] = None
    total_actions: int = 0
    
    # Activity counters
    messages_read: int = 0
    dialogs_opened: int = 0
    profiles_viewed: int = 0
    typing_simulated: int = 0
    contacts_synced: int = 0
    
    # Daily limits based on stage
    daily_actions: int = 0
    daily_limit: int = 10
    last_reset: Optional[str] = None
    
    # Health metrics
    warnings: int = 0
    last_warning: Optional[str] = None
    is_restricted: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "phone": self.phone,
            "stage": self.stage.value,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "total_actions": self.total_actions,
            "messages_read": self.messages_read,
            "dialogs_opened": self.dialogs_opened,
            "profiles_viewed": self.profiles_viewed,
            "daily_actions": self.daily_actions,
            "daily_limit": self.daily_limit,
            "warnings": self.warnings,
            "is_restricted": self.is_restricted,
        }
    
    def get_age_days(self) -> int:
        """Get account age in days."""
        return int((datetime.now().timestamp() - self.created_at) / 86400)
    
    def update_stage(self):
        """Update warmup stage based on age and activity."""
        age_days = self.get_age_days()
        
        if age_days >= 30 and self.total_actions >= 500:
            self.stage = WarmupStage.TRUSTED
            self.daily_limit = 100
        elif age_days >= 15 and self.total_actions >= 200:
            self.stage = WarmupStage.MATURE
            self.daily_limit = 75
        elif age_days >= 8 and self.total_actions >= 100:
            self.stage = WarmupStage.ESTABLISHED
            self.daily_limit = 50
        elif age_days >= 4 and self.total_actions >= 30:
            self.stage = WarmupStage.DEVELOPING
            self.daily_limit = 30
        elif age_days >= 1 or self.total_actions >= 10:
            self.stage = WarmupStage.BEGINNING
            self.daily_limit = 15
        else:
            self.stage = WarmupStage.NEW
            self.daily_limit = 10
    
    def can_perform_action(self) -> bool:
        """Check if account can perform more actions today."""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.last_reset != today:
            self.daily_actions = 0
            self.last_reset = today
        return self.daily_actions < self.daily_limit and not self.is_restricted
    
    def record_action(self):
        """Record an action performed."""
        self.total_actions += 1
        self.daily_actions += 1
        self.last_activity = datetime.now().timestamp()
        self.update_stage()


class WarmupManager:
    """
    Manages account warmup with natural activities:
    - Reading messages
    - Opening dialogs
    - Viewing profiles
    - Simulating typing
    - Syncing contacts
    """
    
    PROFILES_FILE = Path("./data/warmup_profiles.json")
    
    # Natural activities with weights
    ACTIVITIES = [
        ("read_messages", 30),
        ("open_dialogs", 25),
        ("view_profile", 20),
        ("simulate_typing", 15),
        ("sync_contacts", 10),
    ]
    
    def __init__(self):
        self._profiles: Dict[str, WarmupProfile] = {}
        self._load_profiles()
    
    def _load_profiles(self):
        """Load warmup profiles from file."""
        if self.PROFILES_FILE.exists():
            try:
                with open(self.PROFILES_FILE, 'r') as f:
                    data = json.load(f)
                    for p_data in data.get("profiles", []):
                        profile = WarmupProfile(
                            account_id=p_data["account_id"],
                            phone=p_data["phone"],
                            stage=WarmupStage(p_data.get("stage", "new")),
                            created_at=p_data.get("created_at", datetime.now().timestamp()),
                            total_actions=p_data.get("total_actions", 0),
                            messages_read=p_data.get("messages_read", 0),
                            dialogs_opened=p_data.get("dialogs_opened", 0),
                            profiles_viewed=p_data.get("profiles_viewed", 0),
                            daily_actions=p_data.get("daily_actions", 0),
                            daily_limit=p_data.get("daily_limit", 10),
                            warnings=p_data.get("warnings", 0),
                            is_restricted=p_data.get("is_restricted", False),
                        )
                        self._profiles[profile.account_id] = profile
            except Exception as e:
                print(f"Error loading warmup profiles: {e}")
    
    def _save_profiles(self):
        """Save warmup profiles to file."""
        self.PROFILES_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {
                "profiles": [p.to_dict() for p in self._profiles.values()],
                "updated_at": datetime.now().isoformat(),
            }
            with open(self.PROFILES_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving warmup profiles: {e}")
    
    def get_or_create_profile(self, account_id: str, phone: str) -> WarmupProfile:
        """Get existing profile or create new one."""
        if account_id not in self._profiles:
            self._profiles[account_id] = WarmupProfile(
                account_id=account_id,
                phone=phone,
            )
            self._save_profiles()
        return self._profiles[account_id]
    
    def get_profile(self, account_id: str) -> Optional[WarmupProfile]:
        """Get warmup profile for an account."""
        return self._profiles.get(account_id)
    
    def get_all_profiles(self) -> List[Dict[str, Any]]:
        """Get all warmup profiles."""
        return [p.to_dict() for p in self._profiles.values()]
    
    async def perform_warmup_action(
        self,
        client: TelegramClient,
        profile: WarmupProfile
    ) -> Dict[str, Any]:
        """Perform a random warmup action."""
        if not profile.can_perform_action():
            return {
                "success": False,
                "error": "Daily limit reached or account restricted",
                "daily_actions": profile.daily_actions,
                "daily_limit": profile.daily_limit,
            }
        
        # Select random activity based on weights
        activities, weights = zip(*self.ACTIVITIES)
        activity = random.choices(activities, weights=weights)[0]
        
        result = {"activity": activity, "success": False}
        
        try:
            if activity == "read_messages":
                result = await self._read_messages(client, profile)
            elif activity == "open_dialogs":
                result = await self._open_dialogs(client, profile)
            elif activity == "view_profile":
                result = await self._view_profile(client, profile)
            elif activity == "simulate_typing":
                result = await self._simulate_typing(client, profile)
            elif activity == "sync_contacts":
                result = await self._sync_contacts(client, profile)
            
            if result.get("success"):
                profile.record_action()
                self._save_profiles()
                
        except Exception as e:
            result = {"activity": activity, "success": False, "error": str(e)}
        
        return result
    
    async def _read_messages(self, client: TelegramClient, profile: WarmupProfile) -> Dict:
        """Read some messages naturally."""
        try:
            # Get dialogs
            dialogs = await client.get_dialogs(limit=10)
            
            if dialogs:
                # Pick random dialog
                dialog = random.choice(dialogs[:5])
                
                # Human-like delay before reading
                await asyncio.sleep(random.uniform(0.5, 2.0))
                
                # Mark as read
                await client(ReadHistoryRequest(
                    peer=dialog.input_entity,
                    max_id=dialog.message.id if dialog.message else 0
                ))
                
                profile.messages_read += 1
                
                return {
                    "activity": "read_messages",
                    "success": True,
                    "dialog": dialog.name,
                }
        except Exception as e:
            return {"activity": "read_messages", "success": False, "error": str(e)}
        
        return {"activity": "read_messages", "success": False, "error": "No dialogs"}
    
    async def _open_dialogs(self, client: TelegramClient, profile: WarmupProfile) -> Dict:
        """Open and browse dialogs."""
        try:
            # Human-like scroll through dialogs
            await asyncio.sleep(random.uniform(0.3, 1.0))
            
            dialogs = await client.get_dialogs(limit=20)
            
            profile.dialogs_opened += 1
            
            return {
                "activity": "open_dialogs",
                "success": True,
                "count": len(dialogs),
            }
        except Exception as e:
            return {"activity": "open_dialogs", "success": False, "error": str(e)}
    
    async def _view_profile(self, client: TelegramClient, profile: WarmupProfile) -> Dict:
        """View a user profile."""
        try:
            dialogs = await client.get_dialogs(limit=15)
            
            # Find a user dialog
            user_dialogs = [d for d in dialogs if d.is_user and not d.entity.bot]
            
            if user_dialogs:
                dialog = random.choice(user_dialogs)
                
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                # Get full user info
                await client(GetFullUserRequest(dialog.input_entity))
                
                profile.profiles_viewed += 1
                
                return {
                    "activity": "view_profile",
                    "success": True,
                    "user": dialog.name,
                }
        except Exception as e:
            return {"activity": "view_profile", "success": False, "error": str(e)}
        
        return {"activity": "view_profile", "success": False, "error": "No user dialogs"}
    
    async def _simulate_typing(self, client: TelegramClient, profile: WarmupProfile) -> Dict:
        """Simulate typing in a chat (without sending)."""
        try:
            dialogs = await client.get_dialogs(limit=10)
            
            if dialogs:
                dialog = random.choice(dialogs[:5])
                
                # Start typing
                await client(SetTypingRequest(
                    peer=dialog.input_entity,
                    action=SendMessageTypingAction()
                ))
                
                # Type for a bit
                await asyncio.sleep(random.uniform(1.0, 3.0))
                
                profile.typing_simulated += 1
                
                return {
                    "activity": "simulate_typing",
                    "success": True,
                    "dialog": dialog.name,
                }
        except Exception as e:
            return {"activity": "simulate_typing", "success": False, "error": str(e)}
        
        return {"activity": "simulate_typing", "success": False, "error": "No dialogs"}
    
    async def _sync_contacts(self, client: TelegramClient, profile: WarmupProfile) -> Dict:
        """Sync contacts (natural behavior)."""
        try:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            contacts = await client(GetContactsRequest(hash=0))
            
            profile.contacts_synced += 1
            
            return {
                "activity": "sync_contacts",
                "success": True,
                "count": len(contacts.users) if hasattr(contacts, 'users') else 0,
            }
        except Exception as e:
            return {"activity": "sync_contacts", "success": False, "error": str(e)}
    
    async def run_warmup_session(
        self,
        client: TelegramClient,
        profile: WarmupProfile,
        actions: int = 5
    ) -> Dict[str, Any]:
        """Run a complete warmup session with multiple actions."""
        results = []
        successful = 0
        
        for i in range(actions):
            if not profile.can_perform_action():
                break
            
            result = await self.perform_warmup_action(client, profile)
            results.append(result)
            
            if result.get("success"):
                successful += 1
            
            # Natural delay between actions
            if i < actions - 1:
                delay = random.uniform(3.0, 10.0)
                await asyncio.sleep(delay)
        
        return {
            "account_id": profile.account_id,
            "actions_performed": len(results),
            "successful": successful,
            "results": results,
            "profile": profile.to_dict(),
        }
    
    def get_account_readiness(self, account_id: str) -> Dict[str, Any]:
        """Get account readiness for different actions."""
        profile = self._profiles.get(account_id)
        
        if not profile:
            return {
                "ready": False,
                "stage": "unknown",
                "message": "Account not found in warmup system",
            }
        
        profile.update_stage()
        
        readiness = {
            "stage": profile.stage.value,
            "age_days": profile.get_age_days(),
            "total_actions": profile.total_actions,
            "daily_remaining": profile.daily_limit - profile.daily_actions,
            "capabilities": {},
        }
        
        # Define capabilities by stage
        if profile.stage == WarmupStage.NEW:
            readiness["capabilities"] = {
                "messaging": False,
                "reporting": False,
                "joining_groups": False,
                "bulk_actions": False,
            }
            readiness["message"] = "Account too new. Continue warmup activities."
        
        elif profile.stage == WarmupStage.BEGINNING:
            readiness["capabilities"] = {
                "messaging": True,
                "reporting": False,
                "joining_groups": True,
                "bulk_actions": False,
            }
            readiness["message"] = "Limited capabilities. Light usage only."
        
        elif profile.stage == WarmupStage.DEVELOPING:
            readiness["capabilities"] = {
                "messaging": True,
                "reporting": True,
                "joining_groups": True,
                "bulk_actions": False,
            }
            readiness["message"] = "Moderate capabilities. Can start reporting."
        
        elif profile.stage == WarmupStage.ESTABLISHED:
            readiness["capabilities"] = {
                "messaging": True,
                "reporting": True,
                "joining_groups": True,
                "bulk_actions": True,
            }
            readiness["message"] = "Good capabilities. Normal usage allowed."
        
        elif profile.stage in [WarmupStage.MATURE, WarmupStage.TRUSTED]:
            readiness["capabilities"] = {
                "messaging": True,
                "reporting": True,
                "joining_groups": True,
                "bulk_actions": True,
                "high_volume": True,
            }
            readiness["message"] = "Full capabilities. Account is well established."
        
        readiness["ready"] = profile.stage.value not in ["new"]
        
        return readiness
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall warmup statistics."""
        profiles = list(self._profiles.values())
        
        stage_counts = {}
        for stage in WarmupStage:
            stage_counts[stage.value] = len([p for p in profiles if p.stage == stage])
        
        return {
            "total_accounts": len(profiles),
            "stages": stage_counts,
            "total_actions": sum(p.total_actions for p in profiles),
            "restricted_accounts": len([p for p in profiles if p.is_restricted]),
        }


# Global instance
warmup_manager = WarmupManager()
