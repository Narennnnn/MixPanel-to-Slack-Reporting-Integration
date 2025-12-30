"""
Slack Slash Command Handler for Analytics Reports

This Azure Function handles Slack slash commands to generate on-demand reports.
Slack requires a response within 3 seconds, so we:
1. Immediately acknowledge the request
2. Process the report and send via response_url

Usage in Slack:
    /analytics              - Show help
    /analytics daily        - Get daily report (yesterday)
    /analytics weekly       - Get weekly report (last 7 days)
    /analytics biweekly     - Get bi-weekly report (last 14 days)
    /analytics monthly      - Get monthly report (last 30 days)
    /analytics custom 7     - Get report for last N days
"""

import azure.functions as func
import logging
import json
import os
import sys
import threading
import requests
from urllib.parse import parse_qs

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Handle Slack slash command requests."""
    logger.info("Slack slash command received")
    
    try:
        # Parse the form-urlencoded body from Slack
        body = req.get_body().decode('utf-8')
        params = parse_qs(body)
        
        # Extract Slack parameters
        command_text = params.get('text', [''])[0].strip().lower()
        user_name = params.get('user_name', ['someone'])[0]
        response_url = params.get('response_url', [None])[0]
        
        logger.info(f"Command: '{command_text}' from @{user_name}")
        
        # Parse the command
        parts = command_text.split()
        action = parts[0] if parts else 'help'
        
        # Handle help immediately (fast response)
        if action in ['help', '']:
            return create_help_response()
        
        # Validate command before starting background task
        if action not in ['daily', 'weekly', 'biweekly', 'monthly', 'custom']:
            return create_response(
                f"Unknown command: `{action}`\nType `/analytics help` for available commands.",
                is_error=True
            )
        
        # Handle custom days validation
        days = None
        if action == 'custom':
            if len(parts) > 1 and parts[1].isdigit():
                days = int(parts[1])
                if days < 1 or days > 90:
                    return create_response("Please specify between 1 and 90 days.", is_error=True)
            else:
                return create_response(
                    "Usage: `/analytics custom <days>`\nExample: `/analytics custom 7`",
                    is_error=True
                )
        
        # Start background processing
        if response_url:
            thread = threading.Thread(
                target=generate_report_async,
                args=(action, days, response_url)
            )
            thread.start()
        
        # Return immediate acknowledgment (within 3 seconds)
        period_labels = {
            'daily': 'Daily',
            'weekly': 'Weekly', 
            'biweekly': 'Bi-weekly',
            'monthly': 'Monthly',
            'custom': f'Last {days} days'
        }
        
        return func.HttpResponse(
            json.dumps({
                "response_type": "ephemeral",
                "text": f"Generating {period_labels.get(action, action)} report. This may take a few seconds."
            }),
            mimetype="application/json",
            status_code=200
        )
    
    except Exception as e:
        logger.error(f"Error processing slash command: {str(e)}")
        return create_response(f"Something went wrong: {str(e)}", is_error=True)


def generate_report_async(period: str, days: int, response_url: str):
    """Generate report in background and send result to Slack's response_url."""
    try:
        # Import here to avoid import errors during cold start
        from shared.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        # Generate report based on period
        if period == 'daily':
            report = generator.generate_daily_report()
            period_label = "Daily"
        elif period == 'weekly':
            report = generator.generate_weekly_report()
            period_label = "Weekly"
        elif period == 'biweekly':
            report = generator.generate_biweekly_report()
            period_label = "Bi-weekly"
        elif period == 'monthly':
            report = generator.generate_monthly_report()
            period_label = "Monthly"
        elif period == 'custom' and days:
            report = generator.generate_custom_report(days=days)
            period_label = f"Last {days} days"
        else:
            send_to_response_url(response_url, "Invalid report period.", is_error=True)
            return
        
        # Send report to Slack channel via webhook
        generator.send_to_slack(report)
        
        # Send confirmation to user via response_url
        send_to_response_url(
            response_url,
            f"{period_label} report generated and sent to the channel."
        )
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        send_to_response_url(response_url, f"Failed to generate report: {str(e)}", is_error=True)


def send_to_response_url(response_url: str, message: str, is_error: bool = False):
    """Send a message back to Slack via the response_url."""
    try:
        payload = {
            "response_type": "ephemeral",
            "text": f"{'Error: ' if is_error else ''}{message}"
        }
        
        requests.post(
            response_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
    except Exception as e:
        logger.error(f"Failed to send to response_url: {str(e)}")


def create_help_response() -> func.HttpResponse:
    """Return help message showing available commands."""
    help_text = {
        "response_type": "ephemeral",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Analytics Bot Commands"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Available Commands:*"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "`/analytics daily` - Yesterday's report\n"
                        "`/analytics weekly` - Last 7 days\n"
                        "`/analytics biweekly` - Last 14 days\n"
                        "`/analytics monthly` - Last 30 days\n"
                        "`/analytics custom <days>` - Custom period (1-90 days)\n"
                        "`/analytics help` - Show this message"
                    )
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Reports are sent to the channel for everyone to see."
                    }
                ]
            }
        ]
    }
    
    return func.HttpResponse(
        json.dumps(help_text),
        mimetype="application/json",
        status_code=200
    )


def create_response(message: str, is_error: bool = False) -> func.HttpResponse:
    """Return a response message to the user."""
    return func.HttpResponse(
        json.dumps({
            "response_type": "ephemeral",
            "text": f"{'Error: ' if is_error else ''}{message}"
        }),
        mimetype="application/json",
        status_code=200
    )
