"""
Custom Report HTTP Trigger - On-demand report generation
Allows team members to request custom reports via HTTP endpoint
"""
import logging
import azure.functions as func
import os
import sys
import json
from datetime import datetime, timedelta

# Add shared folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.mixpanel_client import MixPanelClient, get_date_range
from shared.slack_client import SlackClient
from shared.report_generator import ReportGenerator


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP Triggered Function for custom/on-demand reports
    
    Query Parameters:
        - period: daily, weekly, biweekly, monthly (default: daily)
        - send_slack: true/false - whether to send to Slack (default: true)
        - from_date: custom start date (YYYY-MM-DD)
        - to_date: custom end date (YYYY-MM-DD)
        - events: comma-separated list of specific events to analyze
    
    Example URLs:
        GET /api/CustomReport?period=weekly
        GET /api/CustomReport?period=daily&send_slack=false
        GET /api/CustomReport?from_date=2025-12-01&to_date=2025-12-28
        POST /api/CustomReport with JSON body
    """
    logging.info('Custom Report HTTP trigger function processed a request')
    
    try:
        # Parse parameters from query string or body
        period = req.params.get('period', 'daily')
        send_slack = req.params.get('send_slack', 'true').lower() == 'true'
        from_date = req.params.get('from_date')
        to_date = req.params.get('to_date')
        events_param = req.params.get('events')
        
        # Also check request body for POST requests
        try:
            req_body = req.get_json()
            period = req_body.get('period', period)
            send_slack = req_body.get('send_slack', send_slack)
            from_date = req_body.get('from_date', from_date)
            to_date = req_body.get('to_date', to_date)
            events_param = req_body.get('events', events_param)
        except:
            pass
        
        # Initialize generator
        report_generator = ReportGenerator()
        
        # Generate report based on parameters
        if from_date and to_date:
            # Custom date range report
            if events_param:
                events = [e.strip() for e in events_param.split(',')]
                report = report_generator.generate_custom_report(
                    events=events,
                    from_date=from_date,
                    to_date=to_date
                )
            else:
                # Use standard report with custom dates
                report = {
                    "period": "custom",
                    "from_date": from_date,
                    "to_date": to_date,
                    "generated_at": datetime.now().isoformat(),
                    "metrics": {},
                    "top_events": report_generator._get_top_events(from_date, to_date),
                    "insights": ["Custom date range report generated"]
                }
        else:
            # Standard period-based report
            report = report_generator.generate_report(period=period)
        
        # Send to Slack if requested
        slack_sent = False
        if send_slack:
            try:
                slack_client = SlackClient()
                slack_sent = slack_client.send_analytics_report(
                    period=report.get("period", period),
                    metrics=report.get("metrics", {}),
                    top_events=report.get("top_events", []),
                    insights=report.get("insights", [])
                )
            except Exception as slack_error:
                logging.error(f"Failed to send to Slack: {slack_error}")
                report["slack_error"] = str(slack_error)
        
        report["slack_sent"] = slack_sent
        
        return func.HttpResponse(
            json.dumps(report, indent=2, default=str),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"Error in custom report: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "message": "Failed to generate report"
            }),
            mimetype="application/json",
            status_code=500
        )
