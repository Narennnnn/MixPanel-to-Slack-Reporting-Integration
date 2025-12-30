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
    
    # Key metrics events for summary
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
                f"Most popular action: *{top_event['event']}* "
                f"with {top_event['count']:,} occurrences"
            )
        
        # User activity insight
        metrics = report["metrics"]
        for key in ["Daily Active Users", "Weekly Active Users", "Monthly Active Users", "Bi-Weekly Active Users"]:
            if key in metrics:
                insights.append(f"Total {key}: *{metrics[key]:,}* users")
                break
        
        # Reewild specific insights
        if "New Signups" in metrics:
            insights.append(f"New user signups: *{metrics['New Signups']:,}* users joined!")
        
        if "Receipts Uploaded" in metrics:
            insights.append(f"Receipts scanned: *{metrics['Receipts Uploaded']:,}* receipts uploaded")
        
        if "Vouchers Redeemed" in metrics:
            insights.append(f"Rewards claimed: *{metrics['Vouchers Redeemed']:,}* vouchers redeemed")
        
        if "Referrals Completed" in metrics:
            insights.append(f"Referral program: *{metrics['Referrals Completed']:,}* successful referrals")
        
        # Period-specific insights
        period = report["period"]
        if period == "weekly":
            insights.append("Review weekly trends to optimize user engagement")
        elif period == "biweekly":
            insights.append("Bi-weekly checkpoint - great for sprint reviews!")
        
        # Default insight if nothing else
        if not insights:
            insights.append("Analytics data collected successfully")
        
        return insights
    
    def generate_custom_report(
        self,
        events: List[str],
        from_date: str,
        to_date: str,
        segment_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a custom report for specific events
        
        Args:
            events: List of event names to analyze
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            segment_by: Property to segment by (optional)
        """
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
