"""
Report Generator - Generates analytics insights from MixPanel data
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .mixpanel_client import MixPanelClient, get_date_range


class ReportGenerator:
    """Generates analytics reports from MixPanel data"""
    
    # Reewild actual events from MixPanel dashboard
    DEFAULT_EVENTS = [
        "PlanetPoints Added",
        "Receipt Uploaded",
        "PlanetPoints Profile Enrolled",
        "Sign Up",
        "User Onboarded",
        "PlanetPoints Product Tracked",
        "$ae_session",
        "Voucher Redeemed",
        "Receipt Failed",
        "PlanetPoints Sign Up",
        "Item Tracked",
        "Receipt Validation Failed",
        "Receipt Autheticity Tracked",
        "SpinWheel Spun",
        "Product Viewed",
        "Referral Completed",
        "Receipt Anomaly Detected"
    ]
    
    KEY_METRIC_EVENTS = {
        "New Signups": "Sign Up",
        "Users Onboarded": "User Onboarded",
        "Receipts Uploaded": "Receipt Uploaded",
        "PlanetPoints Added": "PlanetPoints Added",
        "Vouchers Redeemed": "Voucher Redeemed",
        "Products Tracked": "PlanetPoints Product Tracked",
        "Referrals Completed": "Referral Completed"
    }
    
    def __init__(self, mixpanel_client: Optional[MixPanelClient] = None):
        self.mixpanel = mixpanel_client or MixPanelClient()
        self._slack_client = None
    
    @property
    def slack_client(self):
        """Lazy load Slack client"""
        if self._slack_client is None:
            from .slack_client import SlackClient
            self._slack_client = SlackClient()
        return self._slack_client
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """Generate a daily report (yesterday's data)"""
        return self.generate_report(period="daily")
    
    def generate_weekly_report(self) -> Dict[str, Any]:
        """Generate a weekly report (last 7 days)"""
        return self.generate_report(period="weekly")
    
    def generate_biweekly_report(self) -> Dict[str, Any]:
        """Generate a bi-weekly report (last 14 days)"""
        return self.generate_report(period="biweekly")
    
    def generate_monthly_report(self) -> Dict[str, Any]:
        """Generate a monthly report (last 30 days)"""
        return self.generate_report(period="monthly")
    
    def send_to_slack(self, report: Dict[str, Any]) -> bool:
        """Send a report to Slack"""
        return self.slack_client.send_analytics_report(
            period=report.get("period", "daily"),
            metrics=report.get("metrics", {}),
            top_events=report.get("top_events", []),
            insights=report.get("insights", [])
        )
    
    def generate_report(self, period: str = "daily") -> Dict[str, Any]:
        """
        Generate a complete analytics report
        
        Args:
            period: daily, weekly, biweekly, monthly
        
        Returns:
            Dictionary containing metrics, top_events, and insights
        """
        from_date, to_date = get_date_range(period)
        
        report = {
            "period": period,
            "from_date": from_date,
            "to_date": to_date,
            "generated_at": datetime.now().isoformat(),
            "metrics": {},
            "top_events": [],
            "insights": []
        }
        
        try:
            # Get top events
            report["top_events"] = self._get_top_events(from_date, to_date)
            
            # Calculate key metrics
            report["metrics"] = self._calculate_metrics(from_date, to_date, period)
            
            # Generate insights
            report["insights"] = self._generate_insights(report)
            
        except Exception as e:
            report["error"] = str(e)
            report["insights"].append(f"⚠️ Some data could not be retrieved: {str(e)}")
        
        return report
    
    def _get_top_events(self, from_date: str, to_date: str) -> List[Dict]:
        """Get top events by count"""
        try:
            return self.mixpanel.get_top_events(from_date, to_date, limit=10)
        except Exception as e:
            print(f"Error getting top events: {e}")
            return []
    
    def _calculate_metrics(self, from_date: str, to_date: str, period: str) -> Dict[str, Any]:
        """Calculate key metrics for the report"""
        metrics = {}
        
        # Try to get unique users (DAU/WAU/MAU based on period)
        try:
            user_metric_name = {
                "daily": "Daily Active Users",
                "weekly": "Weekly Active Users",
                "biweekly": "Bi-Weekly Active Users",
                "monthly": "Monthly Active Users"
            }.get(period, "Active Users")
            
            # Try with Reewild session event
            for event in ["$ae_session", "Sign Up", "User Onboarded"]:
                try:
                    data = self.mixpanel.get_unique_users(event, from_date, to_date)
                    if data and "data" in data and "values" in data["data"]:
                        total_users = sum(
                            sum(day_values.values()) 
                            for day_values in data["data"]["values"].values()
                        )
                        if total_users > 0:
                            metrics[user_metric_name] = total_users
                            break
                except:
                    continue
        except Exception as e:
            print(f"Error calculating user metrics: {e}")
        
        # Get counts for Reewild key metric events
        for display_name, event_name in self.KEY_METRIC_EVENTS.items():
            try:
                data = self.mixpanel.get_segmentation_data(
                    event=event_name,
                    from_date=from_date,
                    to_date=to_date,
                    type_="general"
                )
                if data and "data" in data and "values" in data["data"]:
                    total = sum(
                        sum(day_values.values())
                        for day_values in data["data"]["values"].values()
                    )
                    if total > 0:
                        metrics[display_name] = total
            except Exception as e:
                print(f"Error getting {event_name}: {e}")
        
        return metrics
    
    def _generate_insights(self, report: Dict[str, Any]) -> List[str]:
        """Generate human-readable insights from the report data"""
        insights = []
        
        # Top event insight
        if report["top_events"]:
            top_event = report["top_events"][0]
            insights.append(
                f"Top action: {top_event['event']} ({top_event['count']:,} occurrences)"
            )
        
        # User activity insight
        metrics = report["metrics"]
        for key in ["Daily Active Users", "Weekly Active Users", "Monthly Active Users", "Bi-Weekly Active Users"]:
            if key in metrics:
                insights.append(f"{key}: {metrics[key]:,}")
                break
        
        # Reewild specific insights
        if "New Signups" in metrics:
            insights.append(f"New signups: {metrics['New Signups']:,}")
        
        if "Receipts Uploaded" in metrics:
            insights.append(f"Receipts uploaded: {metrics['Receipts Uploaded']:,}")
        
        if "Vouchers Redeemed" in metrics:
            insights.append(f"Vouchers redeemed: {metrics['Vouchers Redeemed']:,}")
        
        if "Referrals Completed" in metrics:
            insights.append(f"Referrals completed: {metrics['Referrals Completed']:,}")
        
        # Period-specific insights
        period = report["period"]
        if period == "weekly":
            insights.append("Week-over-week comparison available in MixPanel")
        elif period == "biweekly":
            insights.append("Bi-weekly summary for sprint review")
        
        # Default insight if nothing else
        if not insights:
            insights.append("Analytics data collected successfully")
        
        return insights
    
    def generate_custom_report(
        self,
        events: List[str] = None,
        from_date: str = None,
        to_date: str = None,
        segment_by: Optional[str] = None,
        days: int = None
    ) -> Dict[str, Any]:
        """
        Generate a custom report for specific events or date range
        
        Args:
            events: List of event names to analyze (optional)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            segment_by: Property to segment by (optional)
            days: Number of days to look back (alternative to from_date/to_date)
        """
        # If days is provided, calculate date range
        if days:
            to_date = datetime.now().strftime("%Y-%m-%d")
            from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            return self.generate_report(period="custom")
        
        # If events are provided, do detailed event analysis
        if events:
            report = {
                "type": "custom",
                "from_date": from_date,
                "to_date": to_date,
                "events_analyzed": events,
                "results": {},
                "generated_at": datetime.now().isoformat()
            }
            
            for event in events:
                try:
                    data = self.mixpanel.get_segmentation_data(
                        event=event,
                        from_date=from_date,
                        to_date=to_date,
                        segment_on=segment_by,
                        type_="general"
                    )
                    report["results"][event] = data
                except Exception as e:
                    report["results"][event] = {"error": str(e)}
            
            return report
        
        # Default: generate standard report for date range
        return self.generate_report(period="custom")
