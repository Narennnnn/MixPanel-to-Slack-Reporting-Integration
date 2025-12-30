"""
Slack Client for sending formatted messages via Webhooks
"""
import os
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime


class SlackClient:
    """Client for sending messages to Slack via Incoming Webhooks"""
    
    def __init__(self):
        self.webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
        self.company_name = os.environ.get("COMPANY_NAME", "Reewild")
        
        if not self.webhook_url:
            raise ValueError("Slack webhook URL not configured. Set SLACK_WEBHOOK_URL")
    
    def send_message(self, text: str, blocks: Optional[List[Dict]] = None) -> bool:
        """
        Send a message to Slack
        
        Args:
            text: Fallback text (shown in notifications)
            blocks: Rich message blocks (optional)
        
        Returns:
            bool: True if successful
        """
        payload = {"text": text}
        
        if blocks:
            payload["blocks"] = blocks
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"Slack API Error: {e}")
            return False
    
    def send_analytics_report(
        self,
        period: str,
        metrics: Dict[str, Any],
        top_events: List[Dict] = None,
        insights: List[str] = None,
        comparisons: Dict[str, Dict] = None,
        mixpanel_url: str = None,
        from_date: str = None,
        to_date: str = None
    ) -> bool:
        """
        Send a formatted analytics report to Slack
        
        Args:
            period: Report period (daily, weekly, biweekly)
            metrics: Dictionary of metric name -> value
            top_events: List of top events with counts
            insights: List of insight strings
            comparisons: Dictionary of metric comparisons with previous period
            mixpanel_url: URL to MixPanel dashboard
            from_date: Start date of the report period
            to_date: End date of the report period
        """
        # Build the report blocks
        blocks = self._build_report_blocks(
            period, metrics, top_events, insights, comparisons, mixpanel_url,
            from_date, to_date
        )
        
        # Fallback text for notifications
        fallback_text = f"{self.company_name} {period.capitalize()} Analytics Report"
        
        return self.send_message(fallback_text, blocks)
    
    def _build_progress_bar(self, current: int, previous: int, width: int = 10) -> str:
        """Build a visual progress bar showing change"""
        if previous == 0:
            return "▓" * width  # Full bar for new metrics
        
        ratio = min(current / previous, 2.0)  # Cap at 200%
        filled = int((ratio / 2.0) * width)
        filled = max(1, min(filled, width))
        
        return "▓" * filled + "░" * (width - filled)
    
    def _format_change_indicator(self, comparison: Dict) -> str:
        """Format a change indicator with arrow and percentage"""
        if not comparison:
            return ""
        
        direction = comparison.get("direction", "flat")
        percent = comparison.get("percent", 0)
        
        if direction == "up":
            return f"↑ {percent}%"
        elif direction == "down":
            return f"↓ {percent}%"
        else:
            return "→ 0%"
    
    def _build_report_blocks(
        self,
        period: str,
        metrics: Dict[str, Any],
        top_events: List[Dict] = None,
        insights: List[str] = None,
        comparisons: Dict[str, Dict] = None,
        mixpanel_url: str = None,
        from_date: str = None,
        to_date: str = None
    ) -> List[Dict]:
        """Build Slack Block Kit blocks for the report"""
        
        comparisons = comparisons or {}
        
        # Format date range for display
        date_range_str = ""
        if from_date and to_date:
            try:
                from_dt = datetime.strptime(from_date, "%Y-%m-%d")
                to_dt = datetime.strptime(to_date, "%Y-%m-%d")
                date_range_str = f"{from_dt.strftime('%b %d')} - {to_dt.strftime('%b %d, %Y')}"
            except:
                date_range_str = f"{from_date} to {to_date}"
        else:
            date_range_str = datetime.now().strftime("%B %d, %Y")
        
        period_label = {
            "daily": "Daily",
            "weekly": "Weekly", 
            "biweekly": "Bi-Weekly",
            "monthly": "Monthly"
        }.get(period, period.capitalize())
        
        blocks = [
            # Header
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{self.company_name} {period_label} Report",
                    "emoji": False
                }
            },
            # Date range context
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*{date_range_str}* • {period_label} Summary"
                    }
                ]
            },
            {"type": "divider"}
        ]
        
        # Key Metrics Section with visual indicators
        if metrics:
            metrics_text = "*Key Metrics*\n"
            for metric_name, value in metrics.items():
                comparison = comparisons.get(metric_name, {})
                change_str = self._format_change_indicator(comparison)
                
                if change_str:
                    metrics_text += f"• {metric_name}: *{value:,}*  `{change_str}`\n"
                else:
                    metrics_text += f"• {metric_name}: *{value:,}*\n"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": metrics_text.strip()
                }
            })
        
        # Top Events Section with visual bars
        if top_events:
            blocks.append({"type": "divider"})
            
            # Find max count for scaling bars
            max_count = max(e['count'] for e in top_events[:5]) if top_events else 1
            
            events_text = "*Top Events*\n"
            for i, event in enumerate(top_events[:5], 1):
                # Scale bar relative to top event
                bar_length = int((event['count'] / max_count) * 8)
                bar = "█" * max(1, bar_length) + "░" * (8 - bar_length)
                events_text += f"`{bar}` {event['event']} — *{event['count']:,}*\n"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": events_text.strip()
                }
            })
        
        # Insights Section
        if insights:
            blocks.append({"type": "divider"})
            
            insights_text = "*Insights*\n"
            for insight in insights:
                insights_text += f"• {insight}\n"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": insights_text.strip()
                }
            })
        
        # MixPanel Link Section
        if mixpanel_url:
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Explore More*\nDive deeper into the data on MixPanel."
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Open MixPanel",
                        "emoji": False
                    },
                    "url": mixpanel_url,
                    "action_id": "open_mixpanel"
                }
            })
        
        # Footer
        blocks.extend([
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"{self.company_name} Analytics • Auto-generated report"
                    }
                ]
            }
        ])
        
        return blocks
    
    def send_error_notification(self, error_message: str, function_name: str) -> bool:
        """Send an error notification to Slack"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⚠️ Analytics Report Error",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Function:* `{function_name}`\n*Error:* {error_message}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    }
                ]
            }
        ]
        
        return self.send_message(f"⚠️ Analytics Error in {function_name}", blocks)
    
    def send_custom_message(self, title: str, message: str, emoji: str = "📢") -> bool:
        """Send a custom formatted message"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🤖 {self.company_name} Analytics Bot"
                    }
                ]
            }
        ]
        
        return self.send_message(f"{emoji} {title}", blocks)
