"""
Smart Analytics & Insights System
Track performance, detect patterns, and optimize operations
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict
import statistics


@dataclass
class TimeSlotStats:
    """Statistics for a time slot."""
    hour: int
    total_reports: int = 0
    successful: int = 0
    failed: int = 0
    avg_response_time: float = 0.0
    
    @property
    def success_rate(self) -> float:
        if self.total_reports == 0:
            return 0.0
        return round((self.successful / self.total_reports) * 100, 2)


@dataclass
class AccountPerformance:
    """Performance metrics for an account."""
    account_id: str
    phone: str
    total_reports: int = 0
    successful: int = 0
    failed: int = 0
    flood_waits: int = 0
    total_flood_wait_seconds: int = 0
    last_used: Optional[str] = None
    health_score: float = 100.0
    
    @property
    def success_rate(self) -> float:
        if self.total_reports == 0:
            return 0.0
        return round((self.successful / self.total_reports) * 100, 2)
    
    def update_health(self):
        """Update health score based on performance."""
        # Start at 100
        score = 100.0
        
        # Deduct for failures
        if self.total_reports > 0:
            failure_rate = self.failed / self.total_reports
            score -= failure_rate * 30  # Up to -30 for all failures
        
        # Deduct for flood waits
        score -= min(self.flood_waits * 5, 30)  # Up to -30 for flood waits
        
        # Deduct for long flood wait times
        if self.flood_waits > 0:
            avg_wait = self.total_flood_wait_seconds / self.flood_waits
            if avg_wait > 60:
                score -= 10
            elif avg_wait > 30:
                score -= 5
        
        self.health_score = max(0, min(100, score))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "phone": self.phone,
            "total_reports": self.total_reports,
            "successful": self.successful,
            "failed": self.failed,
            "success_rate": self.success_rate,
            "flood_waits": self.flood_waits,
            "health_score": round(self.health_score, 1),
            "last_used": self.last_used,
        }


class AnalyticsManager:
    """
    Comprehensive analytics for:
    - Report success rates
    - Best times to report
    - Account performance
    - Target analysis
    - Trend detection
    """
    
    DATA_FILE = Path("./data/analytics.json")
    
    def __init__(self):
        self._reports: List[Dict[str, Any]] = []
        self._account_stats: Dict[str, AccountPerformance] = {}
        self._hourly_stats: Dict[int, TimeSlotStats] = {h: TimeSlotStats(hour=h) for h in range(24)}
        self._target_stats: Dict[str, Dict[str, Any]] = {}
        self._reason_stats: Dict[str, Dict[str, int]] = {}
        self._daily_reports: Dict[str, int] = {}
        
        self._load_data()
    
    def _load_data(self):
        """Load analytics data from file."""
        if self.DATA_FILE.exists():
            try:
                with open(self.DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self._reports = data.get("reports", [])[-10000:]  # Keep last 10k
                    
                    # Rebuild stats from reports
                    self._rebuild_stats()
            except Exception as e:
                print(f"Error loading analytics: {e}")
    
    def _save_data(self):
        """Save analytics data to file."""
        self.DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {
                "reports": self._reports[-10000:],
                "updated_at": datetime.now().isoformat(),
            }
            with open(self.DATA_FILE, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving analytics: {e}")
    
    def _rebuild_stats(self):
        """Rebuild all stats from reports history."""
        for report in self._reports:
            self._update_stats_from_report(report, save=False)
    
    def _update_stats_from_report(self, report: Dict[str, Any], save: bool = True):
        """Update all stats from a single report."""
        account_id = report.get("account_id")
        target = report.get("target")
        reason = report.get("reason")
        success = report.get("success", False)
        timestamp = report.get("timestamp", "")
        flood_wait = report.get("flood_wait", 0)
        
        # Parse hour
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            hour = dt.hour
            date_str = dt.strftime("%Y-%m-%d")
        except:
            hour = 12
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Update hourly stats
        self._hourly_stats[hour].total_reports += 1
        if success:
            self._hourly_stats[hour].successful += 1
        else:
            self._hourly_stats[hour].failed += 1
        
        # Update account stats
        if account_id:
            if account_id not in self._account_stats:
                self._account_stats[account_id] = AccountPerformance(
                    account_id=account_id,
                    phone=report.get("phone", ""),
                )
            
            acc = self._account_stats[account_id]
            acc.total_reports += 1
            if success:
                acc.successful += 1
            else:
                acc.failed += 1
            if flood_wait:
                acc.flood_waits += 1
                acc.total_flood_wait_seconds += flood_wait
            acc.last_used = timestamp
            acc.update_health()
        
        # Update target stats
        if target:
            if target not in self._target_stats:
                self._target_stats[target] = {
                    "target": target,
                    "total_reports": 0,
                    "successful": 0,
                    "first_reported": timestamp,
                }
            self._target_stats[target]["total_reports"] += 1
            if success:
                self._target_stats[target]["successful"] += 1
            self._target_stats[target]["last_reported"] = timestamp
        
        # Update reason stats
        if reason:
            if reason not in self._reason_stats:
                self._reason_stats[reason] = {"total": 0, "successful": 0}
            self._reason_stats[reason]["total"] += 1
            if success:
                self._reason_stats[reason]["successful"] += 1
        
        # Update daily reports
        self._daily_reports[date_str] = self._daily_reports.get(date_str, 0) + 1
        
        if save:
            self._save_data()
    
    def record_report(
        self,
        account_id: str,
        phone: str,
        target: str,
        reason: str,
        success: bool,
        error: Optional[str] = None,
        flood_wait: int = 0,
        response_time: float = 0,
    ):
        """Record a report for analytics."""
        report = {
            "account_id": account_id,
            "phone": phone,
            "target": target,
            "reason": reason,
            "success": success,
            "error": error,
            "flood_wait": flood_wait,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat(),
        }
        
        self._reports.append(report)
        self._update_stats_from_report(report)
    
    def get_best_hours(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Get the best hours for reporting based on success rate."""
        hours = []
        for h, stats in self._hourly_stats.items():
            if stats.total_reports >= 5:  # Minimum sample size
                hours.append({
                    "hour": h,
                    "hour_formatted": f"{h:02d}:00 - {h:02d}:59",
                    "success_rate": stats.success_rate,
                    "total_reports": stats.total_reports,
                })
        
        # Sort by success rate
        hours.sort(key=lambda x: x["success_rate"], reverse=True)
        return hours[:top_n]
    
    def get_worst_hours(self, top_n: int = 3) -> List[Dict[str, Any]]:
        """Get hours to avoid for reporting."""
        hours = []
        for h, stats in self._hourly_stats.items():
            if stats.total_reports >= 5:
                hours.append({
                    "hour": h,
                    "hour_formatted": f"{h:02d}:00 - {h:02d}:59",
                    "success_rate": stats.success_rate,
                    "total_reports": stats.total_reports,
                })
        
        hours.sort(key=lambda x: x["success_rate"])
        return hours[:top_n]
    
    def get_account_rankings(self) -> List[Dict[str, Any]]:
        """Get accounts ranked by performance."""
        accounts = [acc.to_dict() for acc in self._account_stats.values()]
        accounts.sort(key=lambda x: x["health_score"], reverse=True)
        return accounts
    
    def get_best_accounts(self, min_reports: int = 5) -> List[str]:
        """Get list of best performing account IDs."""
        accounts = [
            acc for acc in self._account_stats.values()
            if acc.total_reports >= min_reports and acc.health_score >= 70
        ]
        accounts.sort(key=lambda x: x.health_score, reverse=True)
        return [acc.account_id for acc in accounts]
    
    def get_accounts_needing_rest(self, threshold: float = 50.0) -> List[str]:
        """Get accounts with low health that should rest."""
        return [
            acc.account_id for acc in self._account_stats.values()
            if acc.health_score < threshold
        ]
    
    def get_reason_effectiveness(self) -> List[Dict[str, Any]]:
        """Get effectiveness of each report reason."""
        results = []
        for reason, stats in self._reason_stats.items():
            total = stats["total"]
            successful = stats["successful"]
            rate = (successful / total * 100) if total > 0 else 0
            results.append({
                "reason": reason,
                "total": total,
                "successful": successful,
                "success_rate": round(rate, 2),
            })
        results.sort(key=lambda x: x["success_rate"], reverse=True)
        return results
    
    def get_target_history(self, target: str) -> Optional[Dict[str, Any]]:
        """Get reporting history for a specific target."""
        return self._target_stats.get(target)
    
    def get_daily_trend(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily report counts for trend analysis."""
        trend = []
        for i in range(days - 1, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            trend.append({
                "date": date,
                "reports": self._daily_reports.get(date, 0),
            })
        return trend
    
    def get_insights(self) -> Dict[str, Any]:
        """Get AI-like insights and recommendations."""
        insights = []
        recommendations = []
        
        total_reports = len(self._reports)
        if total_reports == 0:
            return {
                "insights": ["No reports yet. Start reporting to see insights."],
                "recommendations": ["Add accounts and begin reporting."],
            }
        
        # Calculate overall success rate
        successful = sum(1 for r in self._reports if r.get("success"))
        success_rate = (successful / total_reports) * 100
        
        insights.append(f"Overall success rate: {success_rate:.1f}%")
        
        # Best hours insight
        best_hours = self.get_best_hours(3)
        if best_hours:
            hours_str = ", ".join([h["hour_formatted"].split(" ")[0] for h in best_hours])
            insights.append(f"Best reporting hours: {hours_str}")
            recommendations.append(f"Schedule reports around {best_hours[0]['hour_formatted']} for best results")
        
        # Worst hours insight
        worst_hours = self.get_worst_hours(2)
        if worst_hours and worst_hours[0]["success_rate"] < 50:
            hours_str = ", ".join([h["hour_formatted"].split(" ")[0] for h in worst_hours])
            insights.append(f"Avoid reporting at: {hours_str}")
        
        # Account health insight
        tired_accounts = self.get_accounts_needing_rest()
        if tired_accounts:
            insights.append(f"{len(tired_accounts)} accounts need rest")
            recommendations.append("Give low-health accounts a break before using them")
        
        # Reason effectiveness
        reason_stats = self.get_reason_effectiveness()
        if reason_stats:
            best_reason = reason_stats[0]
            if best_reason["total"] >= 10:
                insights.append(f"Most effective reason: {best_reason['reason']} ({best_reason['success_rate']}%)")
        
        # Volume trend
        trend = self.get_daily_trend(7)
        if len(trend) >= 2:
            recent = sum(t["reports"] for t in trend[-3:])
            earlier = sum(t["reports"] for t in trend[:3])
            if recent > earlier * 1.5:
                insights.append("📈 Report volume increasing")
            elif recent < earlier * 0.5:
                insights.append("📉 Report volume decreasing")
        
        return {
            "insights": insights,
            "recommendations": recommendations,
            "success_rate": round(success_rate, 1),
            "total_reports": total_reports,
        }
    
    def get_full_dashboard(self) -> Dict[str, Any]:
        """Get complete analytics dashboard data."""
        return {
            "overview": {
                "total_reports": len(self._reports),
                "total_accounts": len(self._account_stats),
                "total_targets": len(self._target_stats),
            },
            "insights": self.get_insights(),
            "best_hours": self.get_best_hours(5),
            "worst_hours": self.get_worst_hours(3),
            "account_rankings": self.get_account_rankings()[:10],
            "reason_effectiveness": self.get_reason_effectiveness(),
            "daily_trend": self.get_daily_trend(14),
            "accounts_needing_rest": self.get_accounts_needing_rest(),
        }


# Global instance
analytics_manager = AnalyticsManager()
