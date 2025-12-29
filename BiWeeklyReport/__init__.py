"""
Bi-Weekly Report Function - Runs every other Monday at 9 AM
Sends bi-weekly analytics summary to Slack
"""
import logging
import azure.functions as func
import os
import sys
from datetime import datetime

# Add shared folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.mixpanel_client import MixPanelClient
from shared.slack_client import SlackClient
from shared.report_generator import ReportGenerator


def is_biweekly_monday() -> bool:
    """
    Check if current Monday is a bi-weekly Monday
    Uses week number - runs on even weeks (2, 4, 6, etc.)
    """
    week_number = datetime.now().isocalendar()[1]
    return week_number % 2 == 0


def main(mytimer: func.TimerRequest) -> None:
    """
    Azure Function triggered every Monday at 9 AM
    But only processes on bi-weekly (even week) Mondays
    
    Timer trigger: 0 0 9 * * 1 (every Monday 9 AM)
    """
    logging.info('Bi-Weekly Report Function triggered')
    
    # Check if this is a bi-weekly Monday
    if not is_biweekly_monday():
        logging.info("Not a bi-weekly Monday (odd week), skipping...")
        return
    
    try:
        # Initialize clients
        report_generator = ReportGenerator()
        slack_client = SlackClient()
        
        # Generate bi-weekly report
        report = report_generator.generate_report(period="biweekly")
        
        logging.info(f"Generated bi-weekly report: {report['from_date']} to {report['to_date']}")
        
        # Send to Slack
        success = slack_client.send_analytics_report(
            period="biweekly",
            metrics=report.get("metrics", {}),
            top_events=report.get("top_events", []),
            insights=report.get("insights", [])
        )
        
        if success:
            logging.info("Bi-weekly report sent to Slack successfully")
        else:
            logging.error("Failed to send bi-weekly report to Slack")
            
    except Exception as e:
        logging.error(f"Error generating bi-weekly report: {str(e)}")
        
        # Try to send error notification
        try:
            slack_client = SlackClient()
            slack_client.send_error_notification(
                error_message=str(e),
                function_name="BiWeeklyReport"
            )
        except:
            pass
        
        raise
