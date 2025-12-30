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
        insights: List[str] = None
    ) -> bool:
        """
        Send a formatted analytics report to Slack
        
        Args:
            period: Report period (daily, weekly, biweekly)
            metrics: Dictionary of metric name -> value
            top_events: List of top events with counts
            insights: List of insight strings
        """
        # Build the report blocks
        blocks = self._build_report_blocks(period, metrics, top_events, insights)
        
        # Fallback text for notifications
        fallback_text = f"{self.company_name} {period.capitalize()} Analytics Report"
        
        return self.send_message(fallback_text, blocks)
    
    def _build_report_blocks(
        self,
        period: str,
        metrics: Dict[str, Any],
        top_events: List[Dict] = None,
        insights: List[str] = None
    ) -> List[Dict]:
        """Build Slack Block Kit blocks for the report"""
        
        today = datetime.now().strftime("%B %d, %Y")
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
            # Date context
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"{today} • {period_label} Summary"
                    }
                ]
            },
            {"type": "divider"}
        ]
        
        # Key Metrics Section
        if metrics:
            metrics_text = "*Key Metrics*\n"
            for metric_name, value in metrics.items():
                if isinstance(value, dict) and "value" in value:
                    display_value = value["value"]
                    change = value.get("change", "")
                    change_str = f" ({change})" if change else ""
                    metrics_text += f"• {metric_name}: *{display_value:,}*{change_str}\n"
                else:
                    metrics_text += f"• {metric_name}: *{value:,}*\n"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": metrics_text.strip()
                }
            })
        
        # Top Events Section
        if top_events:
            blocks.append({"type": "divider"})
            
            events_text = "*Top Events*\n"
            for i, event in enumerate(top_events[:5], 1):
                events_text += f"{i}. {event['event']} — {event['count']:,}\n"
            
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
            
            insights_text = "*Summary*\n"
            for insight in insights:
                insights_text += f"• {insight}\n"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": insights_text.strip()
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
