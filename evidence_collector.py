"""
Evidence Collector v1
Collects and packages evidence from targets before reporting.
Screenshots profiles, saves messages, exports proof ZIP files.
"""

import asyncio
import json
import time
import os
import zipfile
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from telethon import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.photos import GetUserPhotosRequest
from telethon.tl.functions.messages import GetHistoryRequest, SearchRequest
from telethon.tl.types import (
    InputPeerEmpty, InputMessagesFilterEmpty,
    PeerUser, PeerChannel, PeerChat,
    MessageMediaPhoto, MessageMediaDocument,
    User, Channel, Chat,
)
from telethon.errors import (
    ChannelPrivateError, UserNotParticipantError, ChatAdminRequiredError,
)


class EvidenceType:
    PROFILE = "profile"
    MESSAGES = "messages"
    MEDIA = "media"
    MEMBERS = "members"
    BIO = "bio"
    PHOTOS = "photos"


@dataclass
class EvidenceItem:
    """A single piece of evidence."""
    evidence_type: str
    target: str
    content: Any
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    filename: Optional[str] = None
    size_bytes: int = 0


@dataclass
class EvidencePackage:
    """Complete evidence package for a target."""
    id: str
    target: str
    target_name: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    
    # Collected evidence
    profile_info: Optional[Dict[str, Any]] = None
    bio: Optional[str] = None
    messages: List[Dict[str, Any]] = field(default_factory=list)
    photos: List[str] = field(default_factory=list)  # File paths
    media_files: List[str] = field(default_factory=list)
    member_count: Optional[int] = None
    
    # Metadata
    collected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    collected_by_account: Optional[str] = None
    collection_duration_seconds: float = 0
    evidence_count: int = 0
    
    # Status
    status: str = "pending"  # pending, collecting, complete, failed, exported
    error: Optional[str] = None
    export_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "target": self.target,
            "target_name": self.target_name,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "bio": self.bio,
            "message_count": len(self.messages),
            "photo_count": len(self.photos),
            "media_count": len(self.media_files),
            "member_count": self.member_count,
            "collected_at": self.collected_at,
            "collected_by": self.collected_by_account,
            "duration_seconds": round(self.collection_duration_seconds, 1),
            "evidence_count": self.evidence_count,
            "status": self.status,
            "error": self.error,
            "has_profile": self.profile_info is not None,
            "has_messages": len(self.messages) > 0,
            "has_photos": len(self.photos) > 0,
            "export_path": self.export_path,
        }


class EvidenceCollector:
    """
    Collects evidence from Telegram targets:
    - Profile information (name, bio, username, ID, last seen)
    - Profile photos (downloads)
    - Recent messages (text content + metadata)
    - Media files (photos/documents from messages)
    - Channel/group member count
    
    Everything saved and packaged into exportable ZIP files.
    """
    
    EVIDENCE_DIR = Path("./data/evidence")
    MAX_MESSAGES = 50
    MAX_PHOTOS = 5
    MAX_MEDIA = 10
    
    def __init__(self):
        self._packages: Dict[str, EvidencePackage] = {}
        self._lock = asyncio.Lock()
        self.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        self._load_packages()
    
    def _load_packages(self):
        """Load existing evidence packages metadata."""
        index_file = self.EVIDENCE_DIR / "index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    data = json.load(f)
                    for pkg_data in data.get("packages", []):
                        pkg = EvidencePackage(
                            id=pkg_data["id"],
                            target=pkg_data["target"],
                            target_name=pkg_data.get("target_name"),
                            target_type=pkg_data.get("target_type"),
                            target_id=pkg_data.get("target_id"),
                            bio=pkg_data.get("bio"),
                            messages=pkg_data.get("messages", []),
                            photos=pkg_data.get("photos", []),
                            collected_at=pkg_data.get("collected_at", ""),
                            evidence_count=pkg_data.get("evidence_count", 0),
                            status=pkg_data.get("status", "complete"),
                            export_path=pkg_data.get("export_path"),
                        )
                        if pkg_data.get("profile_info"):
                            pkg.profile_info = pkg_data["profile_info"]
                        self._packages[pkg.id] = pkg
            except Exception as e:
                print(f"Error loading evidence index: {e}")
    
    def _save_index(self):
        """Save evidence package index."""
        try:
            index_file = self.EVIDENCE_DIR / "index.json"
            data = {
                "packages": [p.to_dict() for p in self._packages.values()],
                "updated_at": datetime.utcnow().isoformat(),
            }
            # Add profile_info and messages to the saved data
            for i, pkg in enumerate(self._packages.values()):
                if pkg.profile_info:
                    data["packages"][i]["profile_info"] = pkg.profile_info
                data["packages"][i]["messages"] = pkg.messages[:20]  # Keep first 20 in index
            
            with open(index_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving evidence index: {e}")
    
    # ==================== Collection ====================
    
    async def collect_evidence(
        self,
        client: TelegramClient,
        target: str,
        account_id: str,
        collect_messages: bool = True,
        collect_photos: bool = True,
        collect_media: bool = False,
        max_messages: int = 50,
    ) -> EvidencePackage:
        """
        Collect all available evidence from a target.
        """
        start_time = time.time()
        
        pkg_id = f"ev_{int(time.time())}_{target.replace('@', '').replace('/', '_')[:20]}"
        pkg = EvidencePackage(
            id=pkg_id,
            target=target,
            collected_by_account=account_id,
            status="collecting",
        )
        
        self._packages[pkg_id] = pkg
        
        # Create target directory
        target_dir = self.EVIDENCE_DIR / pkg_id
        target_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Clean target identifier
            clean_target = target.strip()
            if clean_target.startswith("@"):
                clean_target = clean_target[1:]
            if "t.me/" in clean_target:
                clean_target = clean_target.split("t.me/")[-1].split("/")[0].split("?")[0]
            
            # Resolve entity
            entity = await client.get_entity(clean_target)
            
            # Determine type
            if isinstance(entity, User):
                pkg.target_type = "bot" if entity.bot else "user"
                pkg.target_name = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
                pkg.target_id = entity.id
            elif isinstance(entity, Channel):
                pkg.target_type = "group" if entity.megagroup else "channel"
                pkg.target_name = entity.title
                pkg.target_id = entity.id
            elif isinstance(entity, Chat):
                pkg.target_type = "group"
                pkg.target_name = entity.title
                pkg.target_id = entity.id
            
            print(f"📸 Collecting evidence: {pkg.target_name} ({pkg.target_type})")
            
            # 1. Profile info
            await self._collect_profile(client, entity, pkg, target_dir)
            
            # Small human-like delay
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # 2. Messages
            if collect_messages:
                await self._collect_messages(client, entity, pkg, target_dir, max_messages)
                await asyncio.sleep(random.uniform(0.3, 1.0))
            
            # 3. Profile photos
            if collect_photos:
                await self._collect_photos(client, entity, pkg, target_dir)
            
            pkg.status = "complete"
            pkg.collection_duration_seconds = time.time() - start_time
            print(f"   ✅ Evidence collected: {pkg.evidence_count} items in {pkg.collection_duration_seconds:.1f}s")
            
        except ChannelPrivateError:
            pkg.status = "failed"
            pkg.error = "Channel/group is private"
            print(f"   ❌ Cannot access: private")
        except Exception as e:
            pkg.status = "failed"
            pkg.error = str(e)
            print(f"   ❌ Collection failed: {e}")
        
        # Save full evidence to file
        evidence_file = target_dir / "evidence.json"
        try:
            evidence_data = {
                "metadata": pkg.to_dict(),
                "profile": pkg.profile_info,
                "messages": pkg.messages,
                "photos": pkg.photos,
            }
            with open(evidence_file, 'w') as f:
                json.dump(evidence_data, f, indent=2, default=str)
        except Exception as e:
            print(f"   ⚠️ Error saving evidence file: {e}")
        
        self._save_index()
        return pkg
    
    async def _collect_profile(
        self,
        client: TelegramClient,
        entity: Any,
        pkg: EvidencePackage,
        target_dir: Path,
    ):
        """Collect profile information."""
        try:
            profile = {}
            
            if isinstance(entity, User):
                try:
                    full = await client(GetFullUserRequest(entity))
                    user = full.users[0] if full.users else entity
                    full_user = full.full_user
                    
                    profile = {
                        "id": user.id,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "username": user.username,
                        "phone": user.phone,
                        "bio": full_user.about if full_user else None,
                        "is_bot": user.bot,
                        "is_verified": user.verified,
                        "is_scam": user.scam,
                        "is_fake": user.fake,
                        "is_premium": getattr(user, 'premium', False),
                        "is_restricted": user.restricted,
                        "restriction_reason": str(user.restriction_reason) if user.restriction_reason else None,
                        "common_chats_count": full_user.common_chats_count if full_user else None,
                    }
                    
                    pkg.bio = profile.get("bio")
                    
                except Exception:
                    profile = {
                        "id": entity.id,
                        "first_name": entity.first_name,
                        "last_name": entity.last_name,
                        "username": entity.username,
                    }
            
            elif isinstance(entity, Channel):
                try:
                    full = await client(GetFullChannelRequest(entity))
                    full_chat = full.full_chat
                    
                    profile = {
                        "id": entity.id,
                        "title": entity.title,
                        "username": entity.username,
                        "is_megagroup": entity.megagroup,
                        "is_broadcast": entity.broadcast,
                        "is_verified": entity.verified,
                        "is_scam": entity.scam,
                        "is_fake": entity.fake,
                        "is_restricted": entity.restricted,
                        "participants_count": full_chat.participants_count if full_chat else None,
                        "about": full_chat.about if full_chat else None,
                        "linked_chat_id": full_chat.linked_chat_id if full_chat else None,
                    }
                    
                    pkg.bio = profile.get("about")
                    pkg.member_count = profile.get("participants_count")
                    
                except Exception:
                    profile = {
                        "id": entity.id,
                        "title": entity.title,
                        "username": entity.username,
                    }
            
            pkg.profile_info = profile
            pkg.evidence_count += 1
            print(f"   📋 Profile collected")
            
        except Exception as e:
            print(f"   ⚠️ Profile collection failed: {e}")
    
    async def _collect_messages(
        self,
        client: TelegramClient,
        entity: Any,
        pkg: EvidencePackage,
        target_dir: Path,
        max_messages: int = 50,
    ):
        """Collect recent messages from the target."""
        try:
            messages = []
            
            async for msg in client.iter_messages(entity, limit=min(max_messages, self.MAX_MESSAGES)):
                msg_data = {
                    "id": msg.id,
                    "date": msg.date.isoformat() if msg.date else None,
                    "text": msg.text or "",
                    "from_id": msg.from_id.user_id if hasattr(msg.from_id, 'user_id') else None,
                    "has_media": msg.media is not None,
                    "media_type": type(msg.media).__name__ if msg.media else None,
                    "views": msg.views,
                    "forwards": msg.forwards,
                    "reply_to": msg.reply_to.reply_to_msg_id if msg.reply_to else None,
                    "is_pinned": msg.pinned,
                }
                
                messages.append(msg_data)
            
            pkg.messages = messages
            pkg.evidence_count += len(messages)
            print(f"   💬 {len(messages)} messages collected")
            
        except Exception as e:
            print(f"   ⚠️ Message collection failed: {e}")
    
    async def _collect_photos(
        self,
        client: TelegramClient,
        entity: Any,
        pkg: EvidencePackage,
        target_dir: Path,
    ):
        """Download profile photos."""
        try:
            photos_dir = target_dir / "photos"
            photos_dir.mkdir(exist_ok=True)
            
            count = 0
            async for photo in client.iter_profile_photos(entity, limit=self.MAX_PHOTOS):
                try:
                    filename = f"profile_photo_{count + 1}.jpg"
                    filepath = photos_dir / filename
                    
                    await client.download_media(photo, file=str(filepath))
                    
                    if filepath.exists():
                        pkg.photos.append(str(filepath))
                        count += 1
                        
                except Exception:
                    continue
            
            pkg.evidence_count += count
            if count > 0:
                print(f"   📷 {count} profile photos downloaded")
            
        except Exception as e:
            print(f"   ⚠️ Photo collection failed: {e}")
    
    # ==================== Export ====================
    
    async def export_package(self, package_id: str) -> Optional[str]:
        """Export evidence package as ZIP file."""
        pkg = self._packages.get(package_id)
        if not pkg:
            return None
        
        target_dir = self.EVIDENCE_DIR / package_id
        export_dir = self.EVIDENCE_DIR / "exports"
        export_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_target = pkg.target.replace("@", "").replace("/", "_")[:30]
        zip_filename = f"evidence_{safe_target}_{timestamp}.zip"
        zip_path = export_dir / zip_filename
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add evidence.json
                evidence_file = target_dir / "evidence.json"
                if evidence_file.exists():
                    zipf.write(evidence_file, "evidence.json")
                
                # Add summary report
                summary = self._generate_summary_report(pkg)
                zipf.writestr("REPORT.txt", summary)
                
                # Add photos
                photos_dir = target_dir / "photos"
                if photos_dir.exists():
                    for photo_file in photos_dir.iterdir():
                        if photo_file.is_file():
                            zipf.write(photo_file, f"photos/{photo_file.name}")
                
                # Add messages as separate file
                if pkg.messages:
                    messages_txt = self._format_messages(pkg.messages)
                    zipf.writestr("messages.txt", messages_txt)
                
                # Add profile as separate file
                if pkg.profile_info:
                    profile_txt = json.dumps(pkg.profile_info, indent=2, default=str)
                    zipf.writestr("profile.json", profile_txt)
            
            pkg.export_path = str(zip_path)
            pkg.status = "exported"
            self._save_index()
            
            print(f"📦 Evidence exported: {zip_path}")
            return str(zip_path)
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return None
    
    def _generate_summary_report(self, pkg: EvidencePackage) -> str:
        """Generate a human-readable summary report."""
        lines = [
            "=" * 60,
            "EVIDENCE REPORT",
            "=" * 60,
            "",
            f"Target:        {pkg.target}",
            f"Name:          {pkg.target_name or 'Unknown'}",
            f"Type:          {pkg.target_type or 'Unknown'}",
            f"Telegram ID:   {pkg.target_id or 'Unknown'}",
            f"Collected:     {pkg.collected_at}",
            f"Duration:      {pkg.collection_duration_seconds:.1f} seconds",
            "",
            "-" * 60,
            "EVIDENCE SUMMARY",
            "-" * 60,
            "",
        ]
        
        # Profile
        if pkg.profile_info:
            lines.append("PROFILE:")
            for key, value in pkg.profile_info.items():
                if value is not None:
                    lines.append(f"  {key}: {value}")
            lines.append("")
        
        # Bio
        if pkg.bio:
            lines.append(f"BIO: {pkg.bio}")
            lines.append("")
        
        # Stats
        lines.extend([
            f"Messages collected:   {len(pkg.messages)}",
            f"Photos collected:     {len(pkg.photos)}",
            f"Media files:          {len(pkg.media_files)}",
        ])
        
        if pkg.member_count:
            lines.append(f"Member count:         {pkg.member_count}")
        
        lines.extend([
            "",
            "-" * 60,
            f"Total evidence items: {pkg.evidence_count}",
            "=" * 60,
            "",
            f"Report generated: {datetime.utcnow().isoformat()}",
        ])
        
        return "\n".join(lines)
    
    def _format_messages(self, messages: List[Dict[str, Any]]) -> str:
        """Format messages into readable text."""
        lines = [
            "=" * 60,
            "MESSAGE HISTORY",
            "=" * 60,
            "",
        ]
        
        for msg in messages:
            date = msg.get("date", "Unknown date")
            text = msg.get("text", "")
            msg_id = msg.get("id", "?")
            media = f" [MEDIA: {msg.get('media_type')}]" if msg.get("has_media") else ""
            views = f" | Views: {msg['views']}" if msg.get("views") else ""
            
            lines.append(f"[{date}] (ID: {msg_id}){views}")
            if text:
                lines.append(f"  {text}")
            if media:
                lines.append(f"  {media}")
            lines.append("")
        
        return "\n".join(lines)
    
    # ==================== Query ====================
    
    def get_package(self, package_id: str) -> Optional[Dict[str, Any]]:
        """Get a single evidence package."""
        pkg = self._packages.get(package_id)
        if not pkg:
            return None
        result = pkg.to_dict()
        result["profile_info"] = pkg.profile_info
        result["messages_preview"] = pkg.messages[:5]
        return result
    
    def get_all_packages(self) -> List[Dict[str, Any]]:
        """Get all evidence packages."""
        return sorted(
            [p.to_dict() for p in self._packages.values()],
            key=lambda x: x["collected_at"],
            reverse=True,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get evidence collection stats."""
        packages = list(self._packages.values())
        return {
            "total_packages": len(packages),
            "completed": len([p for p in packages if p.status in ["complete", "exported"]]),
            "failed": len([p for p in packages if p.status == "failed"]),
            "total_messages": sum(len(p.messages) for p in packages),
            "total_photos": sum(len(p.photos) for p in packages),
            "exported": len([p for p in packages if p.status == "exported"]),
        }
    
    async def delete_package(self, package_id: str) -> bool:
        """Delete an evidence package and its files."""
        if package_id not in self._packages:
            return False
        
        # Delete directory
        target_dir = self.EVIDENCE_DIR / package_id
        if target_dir.exists():
            import shutil
            shutil.rmtree(target_dir, ignore_errors=True)
        
        del self._packages[package_id]
        self._save_index()
        return True


# Need this import at top level for _collect_photos random delay
import random

# Global instance
evidence_collector = EvidenceCollector()
