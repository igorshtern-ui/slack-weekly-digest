# Slack Weekly Digest System

A comprehensive automated system for generating weekly digests from Slack channels, specifically designed for Nucleus & Trust View workflows at Autodesk.

## 🚀 Features

### Core Functionality
- **Automated Weekly Digests**: Scheduled delivery every Monday at 7:00 AM EDT
- **Multi-Channel Support**: Processes all accessible Slack channels
- **Advanced Analytics**: Resolution tracking, severity analysis, workflow categorization
- **Jira Integration**: Automatic ticket detection and status tracking (MCP ready)

### Advanced Analysis
- **Resolution Confidence Scoring**: 0.0-1.0 based on thread activity and reactions
- **Severity Detection**: High (urgent/critical), Medium (default), Low (minor/enhancement)
- **Workflow Classification**: Nucleus, Trust View, Search, Deployment, Other
- **Question Detection**: Identifies help requests and questions

### Rich Reporting
- **Daily Activity**: Chronological message listing with timestamps
- **Visual Indicators**: Emoji-based severity and status indicators
- **Clickable Links**: Direct Slack message links
- **Comprehensive Statistics**: Response rates, resolution rates, detailed breakdowns

## 📊 Current Configuration

- **Primary Channel**: `#tech-trust-support` (C06K1383Q83)
- **Focus**: Nucleus & Trust View workflows
- **Recipient**: igor.shtern@autodesk.com
- **Schedule**: Every Monday at 7:00 AM EDT

## 🛠️ Installation

### Prerequisites
- Python 3.7+
- Slack Bot Token with appropriate permissions
- Required Python packages (see requirements.txt)

### Setup
1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure your Slack token and team ID in the script
4. Run in test mode first: `python final_weekly_digest_system.py`

## 📁 Project Structure

```
slack-weekly-digest/
├── final_weekly_digest_system.py  # Main digest system
├── requirements.txt               # Python dependencies
├── README.md                     # This file
└── docs/                        # Documentation (if added)
```

## 🔧 Usage

### Test Mode
```python
python final_weekly_digest_system.py
```

### Production Mode
The system includes built-in scheduling for automated weekly delivery.

### Manual Execution
```python
from final_weekly_digest_system import FinalWeeklyDigestSystem

bot = FinalWeeklyDigestSystem(token, team_id)
bot.create_weekly_digest_for_all_channels(
    recipient_email="your-email@autodesk.com",
    days_back=7,
    test_mode=True  # Set to False for live delivery
)
```

## 📈 Digest Output

The system generates comprehensive digests including:

1. **Header**: Channel info, date range, message count
2. **Workflow Breakdown**: Messages by workflow type
3. **Resolution Summary**: Response rates, resolution rates
4. **Jira Integration Status**: Ticket references and lookups
5. **Daily Activity**: Chronological message listing with analysis
6. **Statistics**: Severity breakdown, resolution breakdown
7. **Legends**: Comprehensive emoji and status explanations

## 🔍 Resolution Analysis

- **High Confidence Resolved** (≥0.8): Strong thread activity + reactions
- **Likely Resolved** (0.6-0.8): Moderate engagement
- **Needs Attention** (<0.6): Low engagement, may need follow-up

## 🎫 Jira Integration

- **Ticket Detection**: Regex pattern `[A-Z]+-\d+` (PROJ-123 format)
- **MCP Integration Ready**: Placeholder for MCP Jira tools
- **Caching**: Jira ticket information caching
- **Clickable Links**: Direct links to Jira tickets

## 📝 Logging

Comprehensive logging to `final_digest_system.log` with:
- Channel discovery and access testing
- Message processing and categorization
- Error handling and recovery
- Delivery status and results

## 🔒 Security

- **Token Management**: Secure handling of Slack tokens
- **Error Handling**: Robust error handling for API failures
- **Access Control**: Tests channel access before processing

## 🚀 Production Ready

This system is production-ready with:
- ✅ Comprehensive error handling
- ✅ Robust logging
- ✅ Automated scheduling
- ✅ MCP integration preparation
- ✅ Advanced analytics
- ✅ Rich formatting
- ✅ Flexible operation modes

## 📞 Support

For issues or questions, contact Igor Shtern (igor.shtern@autodesk.com).

## 📄 License

Internal Autodesk project - All rights reserved.