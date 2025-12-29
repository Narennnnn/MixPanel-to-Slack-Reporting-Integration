# Reewild Analytics Reporter 📊

> **Year-End Hackathon 2025** - MixPanel → Slack Reporting Integration

Automated analytics reporting system that fetches insights from MixPanel and sends beautiful reports to Slack.

## 🎯 Features

- **📅 Scheduled Reports**: Daily, Weekly, and Bi-Weekly automated reports
- **🔧 Custom Reports**: On-demand report generation via HTTP endpoint
- **📊 Rich Slack Messages**: Beautiful Block Kit formatted messages
- **☁️ Serverless**: Runs on Azure Functions (cost-effective & scalable)

## 📁 Project Structure

```
ReewildInternalHackathon/
├── shared/                    # Shared modules
│   ├── __init__.py
│   ├── mixpanel_client.py    # MixPanel API client
│   ├── slack_client.py       # Slack webhook client
│   └── report_generator.py   # Report generation logic
├── DailyReport/              # Daily timer trigger (9 AM every day)
├── WeeklyReport/             # Weekly timer trigger (Monday 9 AM)
├── BiWeeklyReport/           # Bi-weekly timer trigger (Every other Monday)
├── CustomReport/             # HTTP trigger for on-demand reports
├── test_local.py             # Local testing script
├── requirements.txt          # Python dependencies
├── host.json                 # Azure Functions host config
├── local.settings.json       # Local dev settings
└── .env                      # Environment variables
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.9+
- Azure Functions Core Tools
- Azure account (for deployment)

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

Update `.env` with your credentials:

```env
# MixPanel
MIXPANEL_USERNAME=your_service_account_username
MIXPANEL_SECRET=your_service_account_secret
MIXPANEL_PROJECT_ID=your_project_id

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 4. Test Locally

```bash
python test_local.py
```

### 5. Run Azure Functions Locally

```bash
func start
```

## ⚙️ Configuration

### MixPanel Setup

1. Go to [MixPanel Settings](https://mixpanel.com/settings/org#serviceaccounts)
2. Create a Service Account with Admin role
3. Copy the username and secret
4. Find your Project ID in Project Settings

### Slack Setup

1. Go to [Slack Apps](https://api.slack.com/apps?new_app=1)
2. Create a new app → From scratch
3. Enable **Incoming Webhooks**
4. Add to your workspace and select a channel
5. Copy the webhook URL

## 📊 Report Schedules

| Report | Schedule | Cron Expression |
|--------|----------|-----------------|
| Daily | Every day at 9 AM | `0 0 9 * * *` |
| Weekly | Monday at 9 AM | `0 0 9 * * 1` |
| Bi-Weekly | Every other Monday at 9 AM | `0 0 9 * * 1` (with logic) |

## 🔧 Custom Reports API

### Endpoint
```
GET/POST /api/CustomReport
```

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | string | daily | daily, weekly, biweekly, monthly |
| `send_slack` | boolean | true | Send report to Slack |
| `from_date` | string | - | Custom start date (YYYY-MM-DD) |
| `to_date` | string | - | Custom end date (YYYY-MM-DD) |
| `events` | string | - | Comma-separated event names |

### Examples

```bash
# Get weekly report
curl "https://your-function.azurewebsites.net/api/CustomReport?period=weekly"

# Custom date range
curl "https://your-function.azurewebsites.net/api/CustomReport?from_date=2025-12-01&to_date=2025-12-28"

# Specific events only
curl "https://your-function.azurewebsites.net/api/CustomReport?events=user_signed_up,product_scanned"
```

## ☁️ Azure Deployment

### 1. Install Azure CLI & Login

```bash
az login
```

### 2. Create Resources

```bash
# Create resource group
az group create --name reewild-analytics-rg --location eastus

# Create storage account
az storage account create --name reewildanalytics --location eastus \
    --resource-group reewild-analytics-rg --sku Standard_LRS

# Create function app
az functionapp create --resource-group reewild-analytics-rg \
    --consumption-plan-location eastus \
    --runtime python --runtime-version 3.9 \
    --functions-version 4 \
    --name reewild-analytics-reporter \
    --storage-account reewildanalytics \
    --os-type linux
```

### 3. Configure App Settings

```bash
az functionapp config appsettings set --name reewild-analytics-reporter \
    --resource-group reewild-analytics-rg \
    --settings \
    MIXPANEL_USERNAME="your_username" \
    MIXPANEL_SECRET="your_secret" \
    MIXPANEL_PROJECT_ID="your_project_id" \
    SLACK_WEBHOOK_URL="your_webhook_url"
```

### 4. Deploy

```bash
func azure functionapp publish reewild-analytics-reporter
```

## 📱 Sample Slack Report

```
📊 Reewild Weekly Analytics Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 December 29, 2025 | Weekly Summary

📈 Key Metrics
• Daily Active Users: 1,234
• New Signups: 89
• Products Scanned: 3,456

🔥 Top Events
🥇 app_opened - 5,678 times
🥈 product_scanned - 3,456 times
🥉 recipe_viewed - 2,345 times

💡 Insights
• Most popular action: app_opened
• 89 new users joined this week!

🤖 Powered by Reewild Analytics Bot | Year-End Hackathon 2025 🎉
```

## 🛠️ Customization

### Add New Events to Track

Edit `shared/report_generator.py`:

```python
DEFAULT_EVENTS = [
    "app_opened",
    "user_signed_up",
    "your_custom_event",  # Add your events here
    ...
]
```

### Change Report Schedule

Edit the `function.json` for each trigger. Cron format:
```
{second} {minute} {hour} {day} {month} {day-of-week}
```

### Customize Slack Message Format

Edit `shared/slack_client.py` → `_build_report_blocks()` method.

## 🤝 Team

Built with ❤️ by **Narendra Maurya** at Reewild Year-End Hackathon 2025

## 📄 License

Internal use only - Reewild
