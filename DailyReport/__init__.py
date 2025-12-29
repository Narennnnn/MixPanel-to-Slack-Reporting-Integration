"""
Daily Report Function - Runs every day at 9 AM
Sends daily analytics summary to Slack
"""
import logging
import azure.functions as func
import os
import sys

# Add shared folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.mixpanel_client import MixPanelClient
from shared.slack_client import SlackClient
from shared.report_generator import ReportGenerator


def main(mytimer: func.TimerRequest) -> None:
    """
    Azure Function triggered daily at 9 AM
    
    Timer trigger: 0 0 9 * * *
    - 0 seconds
    - 0 minutes
    - 9 hours (9 AM)
    - * any day of month
    - * any month
    - * any day of week
    """
    logging.info('Daily Report Function triggered')
    
    try:
        # Initialize clients
        report_generator = ReportGenerator()
        slack_client = SlackClient()
        
        # Generate daily report
        report = report_generator.generate_report(period="daily")
        
        logging.info(f"Generated daily report: {report['from_date']} to {report['to_date']}")
        
        # Send to Slack
        success = slack_client.send_analytics_report(
            period="daily",
            metrics=report.get("metrics", {}),
            top_events=report.get("top_events", []),
            insights=report.get("insights", [])
        )
        
        if success:
            logging.info("Daily report sent to Slack successfully")
        else:
            logging.error("Failed to send daily report to Slack")
            
    except Exception as e:
        logging.error(f"Error generating daily report: {str(e)}")
        
        # Try to send error notification
        try:
            slack_client = SlackClient()
            slack_client.send_error_notification(
                error_message=str(e),
                function_name="DailyReport"
            )
        except:
            pass
        
        raise
