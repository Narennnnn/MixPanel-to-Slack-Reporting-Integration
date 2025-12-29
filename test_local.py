"""
Test Report Locally - For development and testing
Run this script to test the report generation locally
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from shared.mixpanel_client import MixPanelClient, get_date_range
from shared.slack_client import SlackClient
from shared.report_generator import ReportGenerator


def test_mixpanel_connection():
    """Test MixPanel API connection"""
    print("\n" + "="*50)
    print("🔍 Testing MixPanel Connection...")
    print("="*50)
    
    try:
        client = MixPanelClient()
        print(f"✅ MixPanel client initialized")
        print(f"   Username: {client.username[:20]}...")
        print(f"   Project ID: {client.project_id or 'Not set'}")
        
        # Test API call
        from_date, to_date = get_date_range("daily")
        print(f"\n📅 Testing date range: {from_date} to {to_date}")
        
        # Try to get some data
        events = client.export_raw_events(from_date, to_date, limit=10)
        print(f"✅ API Response: Got {len(events)} events")
        
        if events:
            print("\n📊 Sample events:")
            for event in events[:3]:
                print(f"   - {event.get('event', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ MixPanel Error: {e}")
        return False


def test_slack_connection():
    """Test Slack webhook connection"""
    print("\n" + "="*50)
    print("🔍 Testing Slack Connection...")
    print("="*50)
    
    try:
        client = SlackClient()
        webhook_preview = client.webhook_url[:50] + "..." if client.webhook_url else "Not set"
        print(f"✅ Slack client initialized")
        print(f"   Webhook: {webhook_preview}")
        
        # Send test message
        success = client.send_custom_message(
            title="Test Connection",
            message="🧪 This is a test message from Reewild Analytics Bot!\n\nIf you see this, the Slack integration is working! 🎉",
            emoji="🧪"
        )
        
        if success:
            print("✅ Test message sent to Slack successfully!")
        else:
            print("❌ Failed to send test message to Slack")
        
        return success
        
    except Exception as e:
        print(f"❌ Slack Error: {e}")
        return False


def test_report_generation(period="daily"):
    """Test full report generation"""
    print("\n" + "="*50)
    print(f"🔍 Testing {period.capitalize()} Report Generation...")
    print("="*50)
    
    try:
        generator = ReportGenerator()
        report = generator.generate_report(period=period)
        
        print(f"✅ Report generated successfully!")
        print(f"\n📊 Report Summary:")
        print(f"   Period: {report['period']}")
        print(f"   From: {report['from_date']}")
        print(f"   To: {report['to_date']}")
        print(f"   Metrics: {len(report.get('metrics', {}))}")
        print(f"   Top Events: {len(report.get('top_events', []))}")
        print(f"   Insights: {len(report.get('insights', []))}")
        
        if report.get('metrics'):
            print(f"\n📈 Metrics:")
            for name, value in report['metrics'].items():
                print(f"   - {name}: {value}")
        
        if report.get('top_events'):
            print(f"\n🔥 Top Events:")
            for event in report['top_events'][:5]:
                print(f"   - {event['event']}: {event['count']}")
        
        if report.get('insights'):
            print(f"\n💡 Insights:")
            for insight in report['insights']:
                print(f"   - {insight}")
        
        return report
        
    except Exception as e:
        print(f"❌ Report Generation Error: {e}")
        return None


def send_test_report_to_slack(period="daily"):
    """Generate and send a test report to Slack"""
    print("\n" + "="*50)
    print(f"📤 Sending {period.capitalize()} Report to Slack...")
    print("="*50)
    
    try:
        generator = ReportGenerator()
        slack = SlackClient()
        
        # Generate report
        report = generator.generate_report(period=period)
        
        # Send to Slack
        success = slack.send_analytics_report(
            period=period,
            metrics=report.get("metrics", {}),
            top_events=report.get("top_events", []),
            insights=report.get("insights", [])
        )
        
        if success:
            print("✅ Report sent to Slack successfully!")
        else:
            print("❌ Failed to send report to Slack")
        
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n🚀 Reewild Analytics Reporter - Local Test Suite")
    print("=" * 60)
    
    # Check environment variables
    print("\n📋 Environment Check:")
    print(f"   MIXPANEL_USERNAME: {'✅ Set' if os.environ.get('MIXPANEL_USERNAME') else '❌ Missing'}")
    print(f"   MIXPANEL_SECRET: {'✅ Set' if os.environ.get('MIXPANEL_SECRET') else '❌ Missing'}")
    print(f"   MIXPANEL_PROJECT_ID: {'✅ Set' if os.environ.get('MIXPANEL_PROJECT_ID') else '⚠️ Missing (required for queries)'}")
    print(f"   SLACK_WEBHOOK_URL: {'✅ Set' if os.environ.get('SLACK_WEBHOOK_URL') else '❌ Missing'}")
    
    # Run tests
    mixpanel_ok = test_mixpanel_connection()
    slack_ok = test_slack_connection()
    
    if mixpanel_ok:
        report = test_report_generation("daily")
        
        if report and slack_ok:
            print("\n" + "="*50)
            user_input = input("📤 Send this report to Slack? (y/n): ").strip().lower()
            if user_input == 'y':
                send_test_report_to_slack("daily")
    
    print("\n" + "="*60)
    print("🏁 Test Suite Complete!")
    print("="*60)


if __name__ == "__main__":
    main()
