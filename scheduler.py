"""
AI Scheduler v2
Smart task scheduling with optimal time prediction, campaign waves,
timezone awareness, and natural activity distribution.
"""

import asyncio
import json
import math
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
from collections import defaultdict


class TaskType(Enum):
    REPORT = "report"
    WARMUP = "warmup"
    HEALTH_CHECK = "health_check"
    EVIDENCE_COLLECT = "evidence_collect"
    CAMPAIGN_WAVE = "campaign_wave"


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskPriority(Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 8
    URGENT = 10


class DistributionPattern(Enum):
    """How to spread actions across time."""
    UNIFORM = "uniform"         # Equal spacing
    NATURAL = "natural"         # Bell curve around peak hours
    BURST = "burst"             # Concentrated in short window
    SPREAD = "spread"           # Maximum spacing across hours
    RANDOM = "random"           # Random times


# Optimal hours from global analytics (can be updated)
DEFAULT_OPTIMAL_HOURS = [9, 10, 11, 14, 15, 16]
DEFAULT_AVOID_HOURS = [0, 1, 2, 3, 4, 5, 23]


@dataclass
class ScheduledTask:
    """A scheduled task with intelligence."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    task_type: TaskType = TaskType.REPORT
    priority: TaskPriority = TaskPriority.NORMAL
    scheduled_time: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Recurrence
    recurring: bool = False
    recurrence_interval_minutes: Optional[int] = None
    recurrence_count: int = 0
    max_recurrences: Optional[int] = None
    
    # Campaign link
    campaign_id: Optional[str] = None
    wave_number: Optional[int] = None
    
    # Smart scheduling
    auto_scheduled: bool = False
    optimal_score: float = 0.0  # How optimal this time is (0-100)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.task_type.value,
            "priority": self.priority.value,
            "scheduled_time": self.scheduled_time.isoformat(),
            "status": self.status.value,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "recurring": self.recurring,
            "recurrence_interval": self.recurrence_interval_minutes,
            "recurrence_count": self.recurrence_count,
            "campaign_id": self.campaign_id,
            "wave_number": self.wave_number,
            "auto_scheduled": self.auto_scheduled,
            "optimal_score": round(self.optimal_score, 1),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduledTask':
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            task_type=TaskType(data.get("type", "report")),
            priority=TaskPriority(data.get("priority", 5)),
            scheduled_time=datetime.fromisoformat(data["scheduled_time"]) if data.get("scheduled_time") else datetime.now(),
            data=data.get("data", {}),
            status=TaskStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            recurring=data.get("recurring", False),
            recurrence_interval_minutes=data.get("recurrence_interval"),
            campaign_id=data.get("campaign_id"),
            wave_number=data.get("wave_number"),
            auto_scheduled=data.get("auto_scheduled", False),
            optimal_score=data.get("optimal_score", 0),
        )


@dataclass
class Campaign:
    """A multi-wave reporting campaign."""
    id: str = field(default_factory=lambda: f"camp_{str(uuid.uuid4())[:6]}")
    name: str = ""
    targets: List[str] = field(default_factory=list)
    reason: str = "spam"
    message: str = ""
    account_ids: List[str] = field(default_factory=list)
    stealth_level: str = "stealth"
    
    # Wave configuration
    total_waves: int = 3
    hours_between_waves: float = 6.0
    accounts_per_wave: int = 0  # 0 = all accounts
    distribution: DistributionPattern = DistributionPattern.NATURAL
    
    # Status
    status: str = "pending"  # pending, active, paused, completed, cancelled
    current_wave: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    # Results
    total_reports: int = 0
    successful_reports: int = 0
    failed_reports: int = 0
    wave_results: List[Dict[str, Any]] = field(default_factory=list)
    task_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "targets": self.targets,
            "reason": self.reason,
            "account_count": len(self.account_ids),
            "stealth_level": self.stealth_level,
            "total_waves": self.total_waves,
            "hours_between_waves": self.hours_between_waves,
            "distribution": self.distribution.value,
            "status": self.status,
            "current_wave": self.current_wave,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_reports": self.total_reports,
            "successful_reports": self.successful_reports,
            "failed_reports": self.failed_reports,
            "wave_results": self.wave_results,
            "task_count": len(self.task_ids),
        }


class TimeOptimizer:
    """
    Predicts optimal times for actions based on:
    - Historical success rates by hour
    - Day-of-week patterns
    - Avoidance of detection windows
    - Natural human activity patterns
    """
    
    def __init__(self):
        self._hourly_success: Dict[int, List[bool]] = defaultdict(list)
        self._daily_success: Dict[int, List[bool]] = defaultdict(list)  # 0=Mon, 6=Sun
    
    def record_result(self, timestamp: datetime, success: bool):
        """Record a result for learning."""
        self._hourly_success[timestamp.hour].append(success)
        self._daily_success[timestamp.weekday()].append(success)
    
    def get_hour_score(self, hour: int) -> float:
        """Get success score for a specific hour (0-100)."""
        results = self._hourly_success.get(hour, [])
        
        if len(results) < 3:
            # Not enough data, use default knowledge
            if hour in DEFAULT_OPTIMAL_HOURS:
                return 75.0
            elif hour in DEFAULT_AVOID_HOURS:
                return 20.0
            else:
                return 50.0
        
        success_rate = sum(1 for r in results if r) / len(results)
        return success_rate * 100
    
    def get_day_score(self, weekday: int) -> float:
        """Get success score for a day of week (0-100)."""
        results = self._daily_success.get(weekday, [])
        
        if len(results) < 3:
            # Weekdays are generally better
            if weekday < 5:  # Mon-Fri
                return 65.0
            else:
                return 50.0
        
        success_rate = sum(1 for r in results if r) / len(results)
        return success_rate * 100
    
    def find_optimal_time(
        self,
        start_from: Optional[datetime] = None,
        within_hours: int = 24,
    ) -> datetime:
        """Find the best time within the given window."""
        start = start_from or datetime.now()
        
        best_time = start
        best_score = -1
        
        # Check each hour in the window
        for h in range(within_hours):
            candidate = start + timedelta(hours=h)
            hour = candidate.hour
            weekday = candidate.weekday()
            
            score = self.get_hour_score(hour) * 0.7 + self.get_day_score(weekday) * 0.3
            
            # Add small randomness
            score += random.uniform(-5, 5)
            
            if score > best_score:
                best_score = score
                best_time = candidate
        
        # Add random minute offset (don't always schedule at :00)
        best_time = best_time.replace(
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
        )
        
        return best_time
    
    def generate_wave_times(
        self,
        total_waves: int,
        hours_between: float,
        start_from: Optional[datetime] = None,
        pattern: DistributionPattern = DistributionPattern.NATURAL,
    ) -> List[datetime]:
        """Generate optimal times for campaign waves."""
        start = start_from or datetime.now() + timedelta(minutes=5)
        times = []
        
        for wave in range(total_waves):
            if pattern == DistributionPattern.UNIFORM:
                wave_time = start + timedelta(hours=hours_between * wave)
                
            elif pattern == DistributionPattern.NATURAL:
                # Vary interval naturally (±20%)
                actual_interval = hours_between * random.uniform(0.8, 1.2)
                base_time = start + timedelta(hours=actual_interval * wave)
                
                # Try to push toward optimal hours
                optimal_time = self.find_optimal_time(base_time, within_hours=3)
                wave_time = optimal_time
                
            elif pattern == DistributionPattern.BURST:
                # Short intervals (30-60 min between waves)
                interval = random.uniform(0.5, 1.0)
                wave_time = start + timedelta(hours=interval * wave)
                
            elif pattern == DistributionPattern.SPREAD:
                # Maximum spacing (spread across 24h)
                spacing = 24.0 / total_waves
                wave_time = start + timedelta(hours=spacing * wave)
                wave_time = wave_time.replace(minute=random.randint(0, 59))
                
            elif pattern == DistributionPattern.RANDOM:
                # Random within a window
                max_hours = hours_between * total_waves
                random_offset = random.uniform(0, max_hours)
                wave_time = start + timedelta(hours=random_offset)
            
            else:
                wave_time = start + timedelta(hours=hours_between * wave)
            
            times.append(wave_time)
        
        # Sort chronologically
        times.sort()
        return times


class Scheduler:
    """
    AI Scheduler v2 with:
    - Optimal time prediction
    - Campaign management (multi-wave)
    - Distribution patterns
    - Priority queue
    - Recurring tasks
    - Background execution
    """
    
    TASKS_FILE = Path("./data/scheduled_tasks.json")
    CAMPAIGNS_FILE = Path("./data/campaigns.json")
    
    def __init__(self):
        self._tasks: Dict[str, ScheduledTask] = {}
        self._campaigns: Dict[str, Campaign] = {}
        self._task_handlers: Dict[TaskType, Callable] = {}
        self._running = False
        self._loop_task: Optional[asyncio.Task] = None
        self._time_optimizer = TimeOptimizer()
        
        self._load_tasks()
        self._load_campaigns()
    
    def _load_tasks(self):
        if self.TASKS_FILE.exists():
            try:
                with open(self.TASKS_FILE, 'r') as f:
                    data = json.load(f)
                    for td in data.get("tasks", []):
                        task = ScheduledTask.from_dict(td)
                        if task.status == TaskStatus.PENDING:
                            self._tasks[task.id] = task
            except Exception as e:
                print(f"Error loading tasks: {e}")
    
    def _save_tasks(self):
        self.TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {"tasks": [t.to_dict() for t in self._tasks.values()], "updated_at": datetime.now().isoformat()}
            with open(self.TASKS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving tasks: {e}")
    
    def _load_campaigns(self):
        if self.CAMPAIGNS_FILE.exists():
            try:
                with open(self.CAMPAIGNS_FILE, 'r') as f:
                    data = json.load(f)
                    for cd in data.get("campaigns", []):
                        campaign = Campaign(
                            id=cd["id"], name=cd.get("name", ""),
                            targets=cd.get("targets", []),
                            reason=cd.get("reason", "spam"),
                            message=cd.get("message", ""),
                            account_ids=cd.get("account_ids", []),
                            stealth_level=cd.get("stealth_level", "stealth"),
                            total_waves=cd.get("total_waves", 3),
                            hours_between_waves=cd.get("hours_between_waves", 6),
                            status=cd.get("status", "pending"),
                            current_wave=cd.get("current_wave", 0),
                            created_at=cd.get("created_at", ""),
                            total_reports=cd.get("total_reports", 0),
                            successful_reports=cd.get("successful_reports", 0),
                            failed_reports=cd.get("failed_reports", 0),
                            wave_results=cd.get("wave_results", []),
                            task_ids=cd.get("task_ids", []),
                        )
                        try:
                            campaign.distribution = DistributionPattern(cd.get("distribution", "natural"))
                        except ValueError:
                            campaign.distribution = DistributionPattern.NATURAL
                        self._campaigns[campaign.id] = campaign
            except Exception as e:
                print(f"Error loading campaigns: {e}")
    
    def _save_campaigns(self):
        self.CAMPAIGNS_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {"campaigns": [c.to_dict() for c in self._campaigns.values()], "updated_at": datetime.now().isoformat()}
            with open(self.CAMPAIGNS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving campaigns: {e}")
    
    def register_handler(self, task_type: TaskType, handler: Callable):
        self._task_handlers[task_type] = handler
    
    # ==================== Task Scheduling ====================
    
    def schedule_task(
        self,
        task_type: TaskType,
        scheduled_time: datetime,
        data: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        recurring: bool = False,
        recurrence_interval: Optional[int] = None,
        campaign_id: Optional[str] = None,
        wave_number: Optional[int] = None,
    ) -> ScheduledTask:
        """Schedule a task."""
        # Score how optimal this time is
        hour_score = self._time_optimizer.get_hour_score(scheduled_time.hour)
        day_score = self._time_optimizer.get_day_score(scheduled_time.weekday())
        optimal_score = hour_score * 0.7 + day_score * 0.3
        
        task = ScheduledTask(
            task_type=task_type,
            priority=priority,
            scheduled_time=scheduled_time,
            data=data,
            recurring=recurring,
            recurrence_interval_minutes=recurrence_interval,
            campaign_id=campaign_id,
            wave_number=wave_number,
            optimal_score=optimal_score,
        )
        
        self._tasks[task.id] = task
        self._save_tasks()
        
        print(f"📅 Scheduled {task_type.value} for {scheduled_time.strftime('%Y-%m-%d %H:%M')} (optimal: {optimal_score:.0f}%)")
        return task
    
    def schedule_report_auto(
        self,
        targets: List[str],
        reason: str,
        account_ids: List[str],
        message: str = "",
        humanize: bool = True,
        stealth_level: str = "stealth",
        within_hours: int = 24,
    ) -> ScheduledTask:
        """Auto-schedule a report at the optimal time."""
        optimal_time = self._time_optimizer.find_optimal_time(within_hours=within_hours)
        
        task = self.schedule_task(
            task_type=TaskType.REPORT,
            scheduled_time=optimal_time,
            data={
                "targets": targets,
                "reason": reason,
                "account_ids": account_ids,
                "message": message,
                "humanize": humanize,
                "stealth_level": stealth_level,
            },
            priority=TaskPriority.NORMAL,
        )
        task.auto_scheduled = True
        self._save_tasks()
        
        return task
    
    def schedule_warmup(
        self,
        account_id: str,
        actions: int = 5,
        recurring: bool = True,
        interval_minutes: int = 120,
    ) -> ScheduledTask:
        """Schedule a warmup session."""
        # Find good time for warmup (not during report sessions)
        warmup_time = datetime.now() + timedelta(minutes=random.randint(5, 30))
        
        return self.schedule_task(
            task_type=TaskType.WARMUP,
            scheduled_time=warmup_time,
            data={"account_id": account_id, "actions": actions},
            priority=TaskPriority.LOW,
            recurring=recurring,
            recurrence_interval=interval_minutes,
        )
    
    # ==================== Campaign Management ====================
    
    def create_campaign(
        self,
        name: str,
        targets: List[str],
        reason: str,
        account_ids: List[str],
        message: str = "",
        stealth_level: str = "stealth",
        total_waves: int = 3,
        hours_between_waves: float = 6.0,
        accounts_per_wave: int = 0,
        distribution: str = "natural",
    ) -> Campaign:
        """Create a multi-wave reporting campaign."""
        campaign = Campaign(
            name=name,
            targets=targets,
            reason=reason,
            message=message,
            account_ids=account_ids,
            stealth_level=stealth_level,
            total_waves=total_waves,
            hours_between_waves=hours_between_waves,
            accounts_per_wave=accounts_per_wave or len(account_ids),
        )
        
        try:
            campaign.distribution = DistributionPattern(distribution)
        except ValueError:
            campaign.distribution = DistributionPattern.NATURAL
        
        # Generate wave schedule
        wave_times = self._time_optimizer.generate_wave_times(
            total_waves=total_waves,
            hours_between=hours_between_waves,
            pattern=campaign.distribution,
        )
        
        # Create tasks for each wave
        for wave_num, wave_time in enumerate(wave_times):
            # Select accounts for this wave
            if accounts_per_wave and accounts_per_wave < len(account_ids):
                wave_accounts = random.sample(account_ids, accounts_per_wave)
            else:
                wave_accounts = account_ids.copy()
                random.shuffle(wave_accounts)
            
            task = self.schedule_task(
                task_type=TaskType.CAMPAIGN_WAVE,
                scheduled_time=wave_time,
                data={
                    "targets": targets,
                    "reason": reason,
                    "account_ids": wave_accounts,
                    "message": message,
                    "humanize": True,
                    "stealth_level": stealth_level,
                    "wave_number": wave_num + 1,
                    "total_waves": total_waves,
                },
                priority=TaskPriority.HIGH,
                campaign_id=campaign.id,
                wave_number=wave_num + 1,
            )
            campaign.task_ids.append(task.id)
        
        campaign.status = "active"
        campaign.started_at = datetime.utcnow().isoformat()
        
        self._campaigns[campaign.id] = campaign
        self._save_campaigns()
        self._save_tasks()
        
        print(f"🎖️ Campaign '{name}' created: {total_waves} waves, {len(targets)} targets")
        for i, wt in enumerate(wave_times):
            print(f"   Wave {i+1}: {wt.strftime('%Y-%m-%d %H:%M')}")
        
        return campaign
    
    def pause_campaign(self, campaign_id: str) -> bool:
        if campaign_id in self._campaigns:
            self._campaigns[campaign_id].status = "paused"
            # Pause pending tasks
            for tid in self._campaigns[campaign_id].task_ids:
                if tid in self._tasks and self._tasks[tid].status == TaskStatus.PENDING:
                    self._tasks[tid].status = TaskStatus.PAUSED
            self._save_campaigns()
            self._save_tasks()
            return True
        return False
    
    def resume_campaign(self, campaign_id: str) -> bool:
        if campaign_id in self._campaigns:
            self._campaigns[campaign_id].status = "active"
            for tid in self._campaigns[campaign_id].task_ids:
                if tid in self._tasks and self._tasks[tid].status == TaskStatus.PAUSED:
                    self._tasks[tid].status = TaskStatus.PENDING
            self._save_campaigns()
            self._save_tasks()
            return True
        return False
    
    def cancel_campaign(self, campaign_id: str) -> bool:
        if campaign_id in self._campaigns:
            self._campaigns[campaign_id].status = "cancelled"
            for tid in self._campaigns[campaign_id].task_ids:
                if tid in self._tasks and self._tasks[tid].status in [TaskStatus.PENDING, TaskStatus.PAUSED]:
                    self._tasks[tid].status = TaskStatus.CANCELLED
            self._save_campaigns()
            self._save_tasks()
            return True
        return False
    
    # ==================== Task Management ====================
    
    def cancel_task(self, task_id: str) -> bool:
        if task_id in self._tasks:
            task = self._tasks[task_id]
            if task.status in [TaskStatus.PENDING, TaskStatus.PAUSED]:
                task.status = TaskStatus.CANCELLED
                self._save_tasks()
                return True
        return False
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        return sorted(
            [t.to_dict() for t in self._tasks.values() if t.status == TaskStatus.PENDING],
            key=lambda x: x["scheduled_time"],
        )
    
    def get_all_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        tasks = sorted(self._tasks.values(), key=lambda t: t.scheduled_time, reverse=True)
        return [t.to_dict() for t in tasks[:limit]]
    
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        pending = [t for t in self._tasks.values() if t.status == TaskStatus.PENDING]
        if not pending:
            return None
        pending.sort(key=lambda t: t.scheduled_time)
        return pending[0].to_dict()
    
    def get_campaigns(self) -> List[Dict[str, Any]]:
        return sorted(
            [c.to_dict() for c in self._campaigns.values()],
            key=lambda x: x["created_at"],
            reverse=True,
        )
    
    def get_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        c = self._campaigns.get(campaign_id)
        return c.to_dict() if c else None
    
    def get_optimal_hours(self) -> List[Dict[str, Any]]:
        """Get scored hours for scheduling insights."""
        hours = []
        for h in range(24):
            score = self._time_optimizer.get_hour_score(h)
            hours.append({
                "hour": h,
                "label": f"{h:02d}:00",
                "score": round(score, 1),
                "recommended": score >= 60,
            })
        return hours
    
    # ==================== Execution Loop ====================
    
    async def _execute_task(self, task: ScheduledTask):
        handler = self._task_handlers.get(task.task_type)
        if not handler:
            # For campaign waves, use report handler
            if task.task_type == TaskType.CAMPAIGN_WAVE:
                handler = self._task_handlers.get(TaskType.REPORT)
            if not handler:
                task.status = TaskStatus.FAILED
                task.error = f"No handler for {task.task_type.value}"
                self._save_tasks()
                return
        
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self._save_tasks()
        
        try:
            result = await handler(task.data)
            task.result = result
            task.status = TaskStatus.COMPLETED
            
            # Record for optimizer
            success = result.get("success", True) if isinstance(result, dict) else True
            self._time_optimizer.record_result(task.started_at, success)
            
            # Update campaign if linked
            if task.campaign_id and task.campaign_id in self._campaigns:
                campaign = self._campaigns[task.campaign_id]
                campaign.current_wave = max(campaign.current_wave, task.wave_number or 0)
                if isinstance(result, dict):
                    campaign.successful_reports += result.get("successful_reports", 0)
                    campaign.failed_reports += result.get("failed_reports", 0)
                    campaign.total_reports += result.get("total_reports", 0)
                campaign.wave_results.append({
                    "wave": task.wave_number,
                    "result": result,
                    "completed_at": datetime.now().isoformat(),
                })
                # Check if campaign is complete
                all_done = all(
                    self._tasks[tid].status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                    for tid in campaign.task_ids
                    if tid in self._tasks
                )
                if all_done:
                    campaign.status = "completed"
                    campaign.completed_at = datetime.utcnow().isoformat()
                    print(f"🎖️ Campaign '{campaign.name}' completed!")
                
                self._save_campaigns()
            
            print(f"✅ Task {task.id} completed")
            
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            self._time_optimizer.record_result(task.started_at or datetime.now(), False)
            print(f"❌ Task {task.id} failed: {e}")
        
        task.completed_at = datetime.now()
        
        # Handle recurrence
        if task.recurring and task.recurrence_interval_minutes:
            if task.max_recurrences is None or task.recurrence_count < task.max_recurrences:
                next_time = datetime.now() + timedelta(minutes=task.recurrence_interval_minutes)
                new_task = self.schedule_task(
                    task_type=task.task_type,
                    scheduled_time=next_time,
                    data=task.data,
                    priority=task.priority,
                    recurring=True,
                    recurrence_interval=task.recurrence_interval_minutes,
                )
                new_task.recurrence_count = task.recurrence_count + 1
                new_task.max_recurrences = task.max_recurrences
        
        self._save_tasks()
    
    async def _scheduler_loop(self):
        print("🕐 AI Scheduler v2 started")
        
        while self._running:
            now = datetime.now()
            
            # Find ready tasks (sorted by priority)
            ready = sorted(
                [t for t in self._tasks.values() if t.status == TaskStatus.PENDING and t.scheduled_time <= now],
                key=lambda t: t.priority.value,
                reverse=True,
            )
            
            for task in ready:
                print(f"⏰ Executing: {task.id} ({task.task_type.value}) [Priority: {task.priority.value}]")
                await self._execute_task(task)
            
            # Cleanup old tasks
            old = [
                tid for tid, t in self._tasks.items()
                if t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                and t.completed_at and (datetime.now() - t.completed_at).days > 7
            ]
            for tid in old[:50]:
                del self._tasks[tid]
            if old:
                self._save_tasks()
            
            await asyncio.sleep(15)
    
    def start(self):
        if not self._running:
            self._running = True
            self._loop_task = asyncio.create_task(self._scheduler_loop())
    
    def stop(self):
        self._running = False
        if self._loop_task:
            self._loop_task.cancel()
    
    def get_stats(self) -> Dict[str, Any]:
        tasks = list(self._tasks.values())
        campaigns = list(self._campaigns.values())
        
        return {
            "total_tasks": len(tasks),
            "pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),
            "running": len([t for t in tasks if t.status == TaskStatus.RUNNING]),
            "completed": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            "failed": len([t for t in tasks if t.status == TaskStatus.FAILED]),
            "is_running": self._running,
            "total_campaigns": len(campaigns),
            "active_campaigns": len([c for c in campaigns if c.status == "active"]),
        }


# Global instance
scheduler = Scheduler()
