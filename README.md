# RW Analytics Reporter

> **RW: Hackathon 2025** - MixPanel to Slack Reporting Integration

Automated analytics reporting system that fetches insights from MixPanel and sends beautiful reports to Slack.

---

## Overview

This system automatically fetches analytics data from MixPanel and sends formatted reports to Slack at scheduled intervals. Team members receive insights without checking dashboards manually.

### What This System Does

1. **Automatic Scheduling**: Azure Functions runs our code on a schedule - daily at 9 AM, weekly on Mondays, or bi-weekly.

2. **Data Fetching**: When triggered, the system calls MixPanel APIs using service account credentials to get analytics data like user counts, signups, and event activity.

3. **Report Generation**: The data is processed to calculate key metrics, rank top events, and generate simple insights like "89 new users joined this week."

4. **Slack Delivery**: A beautifully formatted message is sent to the team Slack channel via webhook, so everyone sees the update without opening MixPanel.

5. **On-Demand Option**: Team members can also request custom reports for any date range by calling the HTTP endpoint.

---

## Architecture Diagram



[View Architecture Diagram on Excalidraw](https://excalidraw.com/#json=HEurPcOErrfYWYjWE500f,Eng5KocjQT_3D0-AT0OxqA)

---

## System Architecture

```
+------------------------------------------------------------------+
|                      AZURE FUNCTIONS (Serverless)                 |
|  +-------------+ +-------------+ +-------------+ +--------------+ |
|  |   Daily     | |   Weekly    | |  Bi-Weekly  | |    Custom    | |
|  |   Report    | |   Report    | |   Report    | |    Report    | |
|  |  (Timer)    | |  (Timer)    | |  (Timer)    | |   (HTTP)     | |
|  +------+------+ +------+------+ +------+------+ +------+-------+ |
|         |               |               |               |         |
|         +---------------+-------+-------+---------------+         |
|                                 |                                 |
|                    +------------v------------+                    |
|                    |    Report Generator     |                    |
|                    |  (shared/report_gen.py) |                    |
|                    +------------+------------+                    |
|                                 |                                 |
|              +------------------+------------------+               |
|              |                                     |               |
|    +---------v---------+              +------------v------------+ |
|    |  MixPanel Client  |              |     Slack Client        | |
|    | (mixpanel_client) |              |    (slack_client)       | |
|    +---------+---------+              +------------+------------+ |
+--------------|-------------------------------------|---------------+
               |                                     |
               v                                     v
      +----------------+                    +----------------+
      |    MIXPANEL    |                    |      SLACK     |
      |   Query API    |                    |    Webhook     |
      |   Export API   |                    |                |
      +----------------+                    +----------------+
```

---

## Key Components

| Component | File | Purpose |
|-----------|------|---------|
| Azure Functions | `*Report/__init__.py` | Runs code on schedule without managing servers |
| MixPanel Client | `shared/mixpanel_client.py` | Authenticates and fetches data from MixPanel (EU/US/IN) |
| Report Generator | `shared/report_generator.py` | Processes data and creates insights |
| Slack Client | `shared/slack_client.py` | Formats and sends Block Kit messages to Slack |

---

## Features

- **Scheduled Reports**: Daily, Weekly, and Bi-Weekly automated reports
- **Custom Reports**: On-demand report generation via HTTP endpoint
- **Rich Slack Messages**: Beautiful Block Kit formatted messages
- **Serverless**: Runs on Azure Functions (cost-effective and scalable)
- **Error Handling**: Automatic error notifications sent to Slack

---

## Project Structure

```
ReewildInternalHackathon/
├── shared/                    # Core modules (shared by all functions)
│   ├── __init__.py
│   ├── mixpanel_client.py    # MixPanel API client
│   ├── slack_client.py       # Slack webhook client
│   └── report_generator.py   # Report generation logic
├── DailyReport/              # Azure Function - Daily timer trigger
│   ├── __init__.py
│   └── function.json         # Timer: 9 AM every day
├── WeeklyReport/             # Azure Function - Weekly timer trigger
│   ├── __init__.py
│   └── function.json         # Timer: Monday 9 AM
├── BiWeeklyReport/           # Azure Function - Bi-weekly timer trigger
│   ├── __init__.py
│   └── function.json         # Timer: Every other Monday 9 AM
├── CustomReport/             # Azure Function - HTTP trigger
│   ├── __init__.py
│   └── function.json         # On-demand via API call
├── test_local.py             # Local testing script
├── requirements.txt          # Python dependencies
├── host.json                 # Azure Functions host config
├── local.settings.json       # Local dev settings
└── .env                      # Environment variables (secrets)
```

---

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Azure Functions Core Tools (for local testing)
- Azure account (for deployment)
- MixPanel Service Account credentials
- Slack Workspace with webhook access

### 1. Install Dependencies

```bash
# Navigate to project directory
cd /path/to/ReewildInternalHackathon

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Update `.env` with your credentials:

```env
# MixPanel Configuration
MIXPANEL_USERNAME=your_service_account_username
MIXPANEL_SECRET=your_service_account_secret
MIXPANEL_PROJECT_ID=your_project_id

# MixPanel Data Residency (eu, us, or in)
MIXPANEL_REGION=eu

# Slack Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Optional Settings
COMPANY_NAME=Reewild
TIMEZONE=Europe/London
```

### 3. Test Locally

```bash
python test_local.py
```

### 4. Run Azure Functions Locally

```bash
# Set PYTHONPATH for dependencies (required on macOS with Homebrew Python)
export PYTHONPATH="/Users/$(whoami)/Library/Python/3.12/lib/python/site-packages:$PYTHONPATH"

# Start the function app
func start
```

**Note**: Timer triggers require Azure Storage. To test locally without storage, use the HTTP endpoint or `test_local.py`.

---

## Running Locally (macOS Setup)

If you're on macOS with Homebrew Python, you may need to install packages globally:

```bash
# Install packages for Azure Functions worker
pip3.12 install --break-system-packages --user requests python-dotenv

# Or set PYTHONPATH before running
export PYTHONPATH="/Users/$(whoami)/Library/Python/3.12/lib/python/site-packages:$PYTHONPATH"
func start
```

---

## Configuration Guide

### MixPanel Setup

1. Go to [MixPanel Organization Settings](https://mixpanel.com/settings/org#serviceaccounts)
2. Create a Service Account with Admin role
3. Copy the username and secret (save secret immediately, shown only once)
4. Find your Project ID in Project Settings > Overview

### Slack Setup

1. Go to [Create Slack App](https://api.slack.com/apps?new_app=1)
2. Click "Create New App" then "From scratch"
3. Name the app "Reewild Analytics Bot"
4. Select your workspace
5. Navigate to "Incoming Webhooks" in the sidebar
6. Toggle "Activate Incoming Webhooks" to ON
7. Click "Add New Webhook to Workspace"
8. Select the channel for reports (e.g., #analytics)
9. Copy the webhook URL

---

## Report Schedules

| Report | Schedule | Cron Expression | Data Range |
|--------|----------|-----------------|------------|
| Daily | Every day at 9 AM | `0 0 9 * * *` | Previous day |
| Weekly | Monday at 9 AM | `0 0 9 * * 1` | Last 7 days |
| Bi-Weekly | Every other Monday at 9 AM | `0 0 9 * * 1` | Last 14 days |
| Custom | On-demand | N/A | User specified |

---

## Custom Reports API

### Endpoint

```
GET/POST /api/CustomReport
```

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | string | daily | daily, weekly, biweekly, monthly |
| `send_slack` | boolean | true | Whether to send report to Slack |
| `from_date` | string | - | Custom start date (YYYY-MM-DD) |
| `to_date` | string | - | Custom end date (YYYY-MM-DD) |
| `events` | string | - | Comma-separated event names |

### Examples

```bash
# Get daily report and send to Slack
curl "http://localhost:7071/api/CustomReport?period=daily"

# Get weekly report
curl "http://localhost:7071/api/CustomReport?period=weekly"

# Get report without sending to Slack (JSON response only)
curl "http://localhost:7071/api/CustomReport?period=daily&send_slack=false"

# Custom date range
curl "http://localhost:7071/api/CustomReport?from_date=2025-12-01&to_date=2025-12-28"

# Production URL (after deployment)
curl "https://your-function.azurewebsites.net/api/CustomReport?period=weekly"
```

---

## Azure Deployment

### 1. Install Azure CLI and Login

```bash
# Install Azure CLI (macOS)
brew install azure-cli

# Login to Azure
az login
```

### 2. Create Azure Resources

```bash
# Create resource group
az group create --name reewild-analytics-rg --location eastus

# Create storage account (required for Azure Functions)
az storage account create \
    --name reewildanalyticsstorage \
    --location eastus \
    --resource-group reewild-analytics-rg \
    --sku Standard_LRS

# Create function app
az functionapp create \
    --resource-group reewild-analytics-rg \
    --consumption-plan-location eastus \
    --runtime python \
    --runtime-version 3.9 \
    --functions-version 4 \
    --name reewild-analytics-reporter \
    --storage-account reewildanalyticsstorage \
    --os-type linux
```

### 3. Configure App Settings (Environment Variables)

```bash
az functionapp config appsettings set \
    --name reewild-analytics-reporter \
    --resource-group reewild-analytics-rg \
    --settings \
    MIXPANEL_USERNAME="your_username" \
    MIXPANEL_SECRET="your_secret" \
    MIXPANEL_PROJECT_ID="your_project_id" \
    MIXPANEL_REGION="eu" \
    SLACK_WEBHOOK_URL="your_webhook_url" \
    COMPANY_NAME="Reewild"
```

### 4. Deploy the Function App

```bash
func azure functionapp publish reewild-analytics-reporter
```

---

## Sample Slack Report

```
┌──────────────────────────────────────────────────────────┐
│  📊 Reewild Weekly Analytics Report                      │
├──────────────────────────────────────────────────────────┤
│  December 30, 2025 | Weekly Summary                      │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  📈 KEY METRICS                                          │
│  ──────────────────────────────────────────────────────  │
│  👥 Weekly Active Users     25                           │
│  🆕 New Signups             141                          │
│  ✅ Users Onboarded         26                           │
│  🧾 Receipts Uploaded       172                          │
│  🌍 PlanetPoints Added      94                           │
│  🎁 Vouchers Redeemed       9                            │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  🔥 TOP EVENTS                                           │
│  ──────────────────────────────────────────────────────  │
│  1. Email Sent - 8,444 times                             │
│  2. Email Skipped - 6,088 times                          │
│  3. PlanetPoints Product Tracked - 2,628 times           │
│  4. Notifications Disabled - 1,767 times                 │
│  5. Receipt Uploaded - 805 times                         │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  💡 INSIGHTS                                             │
│  ──────────────────────────────────────────────────────  │
│  • Most popular action: Email Sent with 8,444 uses       │
│  • 141 new users joined this week!                       │
│  • 172 receipts scanned for rewards                      │
│  • 9 vouchers redeemed by users                          │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  Powered by Reewild Analytics Bot                        │
│  Built at RW: Hackathon 2025                             │
└──────────────────────────────────────────────────────────┘
```

---

## Customization

### Add New Events to Track

Edit `shared/report_generator.py`:

```python
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
    "Receipt Anomaly Detected",
    "your_custom_event",  # Add your events here
]
```

### Change Report Schedule

Edit the `function.json` file for each trigger. Cron format:

```
{second} {minute} {hour} {day} {month} {day-of-week}
```

Examples:
- `0 0 9 * * *` - Every day at 9:00 AM
- `0 0 9 * * 1` - Every Monday at 9:00 AM
- `0 30 8 * * 1-5` - Weekdays at 8:30 AM

### Customize Slack Message Format

Edit `shared/slack_client.py` and modify the `_build_report_blocks()` method.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'requests'` | Set PYTHONPATH before running: `export PYTHONPATH="/Users/$(whoami)/Library/Python/3.12/lib/python/site-packages:$PYTHONPATH"` |
| MixPanel API returns empty data | Verify Project ID is correct and has data for the date range |
| MixPanel returns 401 Unauthorized | Check service account credentials are correct |
| MixPanel returns 400 Bad Request | Ensure you're using Project ID (numeric), not Project Token |
| Slack message not sending | Check webhook URL is valid and channel exists |
| Timer triggers fail locally | Timer triggers require Azure Storage. Use `test_local.py` or HTTP endpoint instead |
| Azure Function not triggering | Check timer expression and function app logs |
| Rate limit errors (429) | MixPanel has rate limits; the code handles this gracefully |

---

## Tech Stack

- **Runtime**: Python 3.9+
- **Hosting**: Azure Functions (Serverless)
- **APIs**: MixPanel Query API (EU/US/IN data residency supported)
- **Messaging**: Slack Incoming Webhooks
- **Message Format**: Slack Block Kit

---

## Metrics Tracked

| Metric | MixPanel Event |
|--------|----------------|
| New Signups | `Sign Up` |
| Users Onboarded | `User Onboarded` |
| Receipts Uploaded | `Receipt Uploaded` |
| PlanetPoints Added | `PlanetPoints Added` |
| Vouchers Redeemed | `Voucher Redeemed` |
| Products Tracked | `PlanetPoints Product Tracked` |
| Referrals Completed | `Referral Completed` |

---

## Author

Built by **Narendra Maurya** at RW: Hackathon 2025

---
