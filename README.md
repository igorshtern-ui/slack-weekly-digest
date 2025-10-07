# Slack Weekly Digest System

A comprehensive Python system for generating automated weekly digests from Slack channels, focusing on Nucleus and Trust View automation workflows.

## 🎯 Overview

The Slack Weekly Digest System automatically monitors Slack channels for automation workflow messages, categorizes them by type and severity, tracks resolution status, and generates comprehensive weekly summaries. The system is specifically designed to handle Nucleus and Trust View automation workflows from Autodesk's internal systems.

## ✨ Key Features

### 🔍 **Smart Message Filtering**
- **Workflow-Specific**: Only includes messages from Nucleus and Trust View automation workflows
- **Request Type Detection**: Extracts and categorizes based on Request Type field
- **Bot Message Processing**: Handles automation bot messages while extracting real user information

### 📊 **Comprehensive Analysis**
- **Resolution Tracking**: Analyzes message resolution status with confidence scoring
- **Severity Classification**: Categorizes messages by priority (High/Medium/Low)
- **User Activity Analysis**: Tracks user engagement and activity patterns
- **Daily Activity Breakdown**: Shows message distribution by day

### 🎨 **Professional Output Format**
- **One-liner Summary**: Clean main message with key statistics
- **Detailed Thread Reply**: Comprehensive analysis in organized format
- **@ User Names**: Shows actual user names (e.g., "@Kerby Geffrard")
- **Compressed Status**: One-line resolution status summary

### 🔧 **Advanced Features**
- **Jira Integration Ready**: Extracts Jira ticket references (placeholder for MCP integration)
- **Automated Scheduling**: Built-in weekly execution capability
- **Error Handling**: Robust error handling and logging
- **Configurable Timeframes**: Adjustable lookback periods

## 🚀 Installation

### Prerequisites
- Python 3.7+
- Slack Bot Token with appropriate permissions
- Access to Autodesk Slack workspace

### Setup Steps

1. **Clone the repository:**
```bash
git clone https://github.com/igorshtern-ui/slack-weekly-digest.git
cd slack-weekly-digest-test
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your Slack credentials
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_TEAM_ID=your-team-id
RECIPIENT_EMAIL=your-email@autodesk.com
```

### Slack Bot Permissions

The bot requires the following Slack permissions:
- `channels:history` - Read channel messages
- `channels:read` - Access channel information
- `chat:write` - Post messages
- `users:read` - Get user information
- `users.profile:read` - Access user profiles
- `reactions:read` - Read message reactions

## 📱 Usage

### Manual Execution

Run the system manually for testing:

```bash
python final_weekly_digest_system.py
```

### Automated Scheduling

For production use, the system includes built-in scheduling:

```python
from final_weekly_digest_system import FinalWeeklyDigestSystem

bot = FinalWeeklyDigestSystem(token, team_id)
bot.start_scheduler()  # Runs every Monday at 9 AM
```

### Custom Channel Configuration

To target specific channels, modify the channel ID in the code:

```python
# Example: Target tech-trust-support channel
test_channel_id = 'C06K1383Q83'
digest_content = bot.create_weekly_digest_for_channel(
    test_channel_id, 
    recipient_email, 
    days_back=7, 
    test_mode=False
)
```

## 📋 Output Format

### Main Message (One-liner)
```
📊 Weekly Digest: 4 messages | Nucleus: 3, Trust View: 1 | Medium: 4
```

### Detailed Thread Reply

```
📊 **Weekly Digest - Nucleus & Trust View Automation**
📢 **#tech-trust-support** | 📅 Sep 30 - Oct 07, 2025
📈 **4 messages**

**🔑 Workflow Breakdown:**
• Nucleus: 3 messages
• Trust View: 1 message

**📊 Resolution Status:** 4 total | 4 resolved | 0 need attention

**📅 Daily Activity:**
• Monday, Oct 06: 1 messages
  1. **@Rahul** | Type: Nucleus | 🟡 Medium | ✅ RESOLVED
     Requesting access
     to Nucleus

• Friday, Oct 03: 2 messages
  1. **@david.mackarill** | Type: Trust View | 🟡 Medium | ✅ RESOLVED
     Our BIM360 nucleus service is showing 99.685 availability I would like to understand how this figure is obtained. In SNOW i can only see 52 minutes of
     business duration downtime, this gives us 99.88% over 30days Availability % = ((Total Time - Downtime) / Total Time) × 100 43,200 - 52 = 43,148 (

  2. **@Kerby Geffrard** | Type: Nucleus | 🟡 Medium | ✅ RESOLVED
     At the Nucleus meeting, I got told we need to contact
     the Nucleus team to have tickets automatically created on new vulnerabilities.

**🚨 Severity:**
• 🟡 Medium: 4

**🔍 Legends:**
**Severity:** 🔴 High | 🟡 Medium | 🔵 Low
**Resolution:** ✅ Resolved | 🔄 Likely | ❓ Needs Attention
**Thread:** 📝 Has responses

🤖 *Auto-generated weekly digest*
🔍 *Filtered for: Nucleus & Trust View workflows only*
```

## 🔧 Technical Details

### Message Processing Pipeline

1. **Message Retrieval**: Fetches messages from specified Slack channels
2. **Workflow Filtering**: Identifies Nucleus and Trust View automation messages
3. **User Extraction**: Extracts actual user information from bot messages
4. **Content Analysis**: Analyzes message content for severity and resolution status
5. **Digest Generation**: Creates formatted digest with statistics and details
6. **Slack Posting**: Sends one-liner and detailed thread reply

### Workflow Categorization Logic

The system uses sophisticated logic to categorize messages:

```python
# Extract Request Type field
if 'request type:' in text:
    request_type = extract_request_type(text)
    
    if 'nucleus' in request_type:
        workflow = "Nucleus"
    elif 'trust view' in request_type:
        workflow = "Trust View"
    elif 'trust dashboard' in request_type:
        workflow = "Trust View"
```

### Resolution Confidence Scoring

Messages are analyzed for resolution status based on:
- **Thread Activity**: Presence of thread responses (+0.3)
- **Reactions**: Number of reactions (+0.1 per reaction)
- **Confidence Levels**:
  - ✅ **Resolved**: ≥0.8 confidence
  - 🔄 **Likely**: 0.6-0.8 confidence
  - ❓ **Needs Attention**: <0.6 confidence

### User Name Extraction

The system extracts actual user names from bot messages:

```python
# Pattern: "New request from <@USER_ID> via <@BOT_ID>"
pattern = r'New request from <@([A-Z0-9]+)> via'
match = re.search(pattern, text)
if match:
    user_id = match.group(1)
    user_name = get_user_info(user_id)  # Convert to readable name
```

## 🎨 Customization

### Adding New Workflow Types

To support additional workflow types, modify the categorization logic:

```python
elif 'new_workflow' in request_type:
    workflow = "New Workflow"
```

### Adjusting Time Periods

Change the lookback period:

```python
# 30-day lookback instead of 7 days
digest_content = bot.create_weekly_digest_for_channel(
    channel_id, 
    recipient_email, 
    days_back=30,  # Changed from 7
    test_mode=False
)
```

### Custom Channel Targeting

Add multiple channels:

```python
channels = ['C06K1383Q83', 'C09GY0TUNBS']  # Multiple channels
for channel_id in channels:
    digest_content = bot.create_weekly_digest_for_channel(
        channel_id, 
        recipient_email, 
        days_back=7, 
        test_mode=False
    )
```

## 📊 Statistics and Metrics

The system tracks and reports:

- **Total Messages**: Count of automation workflow messages
- **Workflow Breakdown**: Distribution by workflow type
- **Resolution Status**: Resolved vs. needs attention
- **Severity Analysis**: High/Medium/Low priority distribution
- **Daily Activity**: Message distribution by day
- **User Activity**: Individual user contribution analysis

## 🔍 Troubleshooting

### Common Issues

1. **"No messages found"**
   - Check channel permissions
   - Verify bot is member of target channel
   - Confirm message filtering criteria

2. **"Missing scope" errors**
   - Ensure bot has required Slack permissions
   - Check token validity

3. **Incorrect workflow categorization**
   - Verify Request Type field format
   - Check case sensitivity in text processing

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance

- **Processing Speed**: ~1-2 seconds per 100 messages
- **Memory Usage**: Minimal memory footprint
- **API Limits**: Respects Slack API rate limits
- **Scalability**: Handles channels with 1000+ messages

## 🔒 Security

- **Token Management**: Uses environment variables for sensitive data
- **Permission Scope**: Minimal required permissions
- **Data Privacy**: Only processes public channel messages
- **No Data Storage**: No persistent data storage

## 📝 Requirements

### Python Dependencies
```
slack-sdk>=3.21.0
python-dotenv>=1.0.0
pytz>=2023.3
schedule>=1.2.0
```

### System Requirements
- Python 3.7+
- Internet connection for Slack API
- Slack workspace access

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For issues and questions:
- Create an issue in the GitHub repository
- Contact the development team
- Check the troubleshooting section above

## 🔄 Version History

- **v2.0** - Complete rewrite with enhanced filtering and formatting
- **v1.5** - Added user name extraction and resolution tracking
- **v1.0** - Initial release with basic digest functionality

---

**Built with ❤️ for Autodesk's automation workflow monitoring**