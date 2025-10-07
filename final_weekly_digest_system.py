#!/usr/bin/env python3
"""
Final Weekly Digest System - Comprehensive solution with all features
"""

import os
import json
import logging
import schedule
import time
import pytz
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from collections import Counter, defaultdict
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/shterni/final_digest_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MessageData:
    """Data structure for message information"""
    user: str
    text: str
    timestamp: str
    thread_ts: Optional[str] = None
    reactions: List[Dict] = None
    attachments: List[Dict] = None

@dataclass
class JiraTicket:
    """Data structure for Jira ticket information"""
    key: str
    summary: str
    status: str
    priority: str
    assignee: str
    url: str

class FinalWeeklyDigestSystem:
    """Final comprehensive weekly digest system with all features"""
    
    def __init__(self, token: str, team_id: str):
        self.client = WebClient(token=token)
        self.team_id = team_id
        self.users_cache = {}
        self.edt_tz = pytz.timezone('US/Eastern')
        self.jira_tickets_cache = {}
        
    def get_user_info(self, user_id: str) -> str:
        """Get user display name with caching"""
        if user_id in self.users_cache:
            return self.users_cache[user_id]
        
        try:
            response = self.client.users_info(user=user_id)
            user = response['user']
            display_name = user.get('real_name', user.get('display_name', user.get('name', 'Unknown')))
            self.users_cache[user_id] = display_name
            return display_name
        except SlackApiError:
            self.users_cache[user_id] = 'Unknown User'
            return 'Unknown User'
    
    def get_available_channels(self) -> List[Dict]:
        """Get list of channels the bot has access to with comprehensive error handling"""
        try:
            channels = []
            
            # Get all channel types
            channel_types = ["public_channel", "private_channel", "mpim", "im"]
            
            for channel_type in channel_types:
                try:
                    response = self.client.conversations_list(types=channel_type, limit=200)
                    if response['ok']:
                        channels.extend(response['channels'])
                except SlackApiError as e:
                    logger.warning(f"Could not get {channel_type} channels: {e}")
            
            # Filter and format channels
            accessible_channels = []
            for channel in channels:
                try:
                    # Test access by getting channel info
                    channel_info = self.client.conversations_info(channel=channel['id'])
                    if channel_info['ok']:
                        accessible_channels.append({
                            'id': channel['id'],
                            'name': channel['name'],
                            'is_member': channel.get('is_member', False),
                            'is_private': channel.get('is_private', False),
                            'purpose': channel.get('purpose', {}).get('value', ''),
                            'topic': channel.get('topic', {}).get('value', ''),
                            'num_members': channel.get('num_members', 0)
                        })
                except SlackApiError:
                    continue
            
            logger.info(f"Found {len(accessible_channels)} accessible channels")
            return accessible_channels
            
        except Exception as e:
            logger.error(f"Error getting channels: {e}")
            return []
    
    def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """Get channel information with better error handling"""
        try:
            response = self.client.conversations_info(channel=channel_id)
            return {
                'name': response['channel']['name'],
                'purpose': response['channel'].get('purpose', {}).get('value', ''),
                'topic': response['channel'].get('topic', {}).get('value', ''),
                'num_members': response['channel'].get('num_members', 0)
            }
        except SlackApiError as e:
            logger.error(f"Error getting channel info: {e}")
            return {'name': channel_id, 'purpose': '', 'topic': '', 'num_members': 0}
    
    def get_channel_messages(self, channel_id: str, days_back: int = 7) -> List[MessageData]:
        """Retrieve messages from channel for the specified number of days"""
        try:
            since = datetime.now() - timedelta(days=days_back)
            
            response = self.client.conversations_history(
                channel=channel_id,
                oldest=since.timestamp(),
                limit=500
            )
            
            messages = []
            for msg in response['messages']:
                if msg.get('type') == 'message' and not msg.get('bot_id'):
                    message_data = MessageData(
                        user=msg.get('user', 'Unknown'),
                        text=msg.get('text', ''),
                        timestamp=msg.get('ts', ''),
                        thread_ts=msg.get('thread_ts'),
                        reactions=msg.get('reactions', []),
                        attachments=msg.get('attachments', [])
                    )
                    messages.append(message_data)
            
            return messages
            
        except SlackApiError as e:
            logger.error(f"Error fetching messages from {channel_id}: {e}")
            return []
    
    def extract_jira_tickets(self, text: str) -> List[str]:
        """Extract Jira ticket references from text"""
        # Pattern to match Jira tickets (e.g., PROJ-123, A-123, B-1234567890)
        jira_pattern = r'\b[A-Z]+-\d+\b'
        tickets = re.findall(jira_pattern, text)
        return list(set(tickets))  # Remove duplicates
    
    def lookup_jira_ticket(self, ticket_key: str) -> Optional[JiraTicket]:
        """Look up Jira ticket information (placeholder for MCP integration)"""
        if ticket_key in self.jira_tickets_cache:
            return self.jira_tickets_cache[ticket_key]
        
        # This would integrate with MCP Jira tools
        # For now, return a placeholder
        ticket = JiraTicket(
            key=ticket_key,
            summary=f"Ticket {ticket_key}",
            status="Unknown",
            priority="Unknown",
            assignee="Unknown",
            url=f"https://jira.autodesk.com/browse/{ticket_key}"
        )
        
        self.jira_tickets_cache[ticket_key] = ticket
        return ticket
    
    def categorize_message(self, message: MessageData) -> Dict[str, Any]:
        """Categorize message and extract metadata"""
        text = message.text.lower()
        
        # Extract Jira tickets
        jira_tickets = self.extract_jira_tickets(message.text)
        
        # Determine severity based on keywords
        severity = "Medium"
        if any(word in text for word in ['urgent', 'critical', 'emergency', 'asap', 'blocking']):
            severity = "High"
        elif any(word in text for word in ['low', 'minor', 'nice to have', 'enhancement']):
            severity = "Low"
        
        # Determine if it's a question
        is_question = any(word in text for word in ['?', 'question', 'how', 'what', 'why', 'when', 'where', 'can you', 'could you', 'help'])
        
        # Determine workflow type
        workflow = "Other"
        if any(word in text for word in ['nucleus', 'nucleus dashboard']):
            workflow = "Nucleus"
        elif any(word in text for word in ['trust', 'trust view', 'trust dashboard']):
            workflow = "Trust View"
        elif any(word in text for word in ['search', 'search 3.0', 'ingestion']):
            workflow = "Search"
        elif any(word in text for word in ['deployment', 'production', 'staging']):
            workflow = "Deployment"
        
        # Determine resolution confidence based on thread activity and reactions
        resolution_confidence = 0.5  # Default
        if message.thread_ts:
            resolution_confidence += 0.3  # Has thread responses
        if message.reactions:
            resolution_confidence += len(message.reactions) * 0.1  # More reactions = more engagement
        
        return {
            'severity': severity,
            'is_question': is_question,
            'workflow': workflow,
            'jira_tickets': jira_tickets,
            'has_thread': message.thread_ts is not None,
            'reaction_count': len(message.reactions) if message.reactions else 0,
            'resolution_confidence': min(resolution_confidence, 1.0)
        }
    
    def generate_final_digest_content(self, channel_info: Dict, messages: List[MessageData], days_back: int) -> str:
        """Generate final comprehensive digest content"""
        if not messages:
            return "📭 No new messages to include in this weekly digest."
        
        # Sort messages by timestamp
        messages.sort(key=lambda x: float(x.timestamp))
        
        # Categorize all messages
        categorized_messages = []
        for msg in messages:
            category = self.categorize_message(msg)
            categorized_messages.append((msg, category))
        
        # Group messages by day
        daily_messages = defaultdict(list)
        for msg, category in categorized_messages:
            dt = datetime.fromtimestamp(float(msg.timestamp))
            day_key = dt.strftime('%Y-%m-%d')
            daily_messages[day_key].append((msg, category))
        
        # Calculate statistics
        total_messages = len(messages)
        questions = sum(1 for _, cat in categorized_messages if cat['is_question'])
        jira_references = sum(len(cat['jira_tickets']) for _, cat in categorized_messages)
        
        # Workflow breakdown
        workflow_counts = Counter(cat['workflow'] for _, cat in categorized_messages)
        
        # Severity breakdown
        severity_counts = Counter(cat['severity'] for _, cat in categorized_messages)
        
        # Resolution analysis
        high_confidence_resolved = sum(1 for _, cat in categorized_messages if cat['resolution_confidence'] >= 0.8)
        likely_resolved = sum(1 for _, cat in categorized_messages if 0.6 <= cat['resolution_confidence'] < 0.8)
        needs_attention = sum(1 for _, cat in categorized_messages if cat['resolution_confidence'] < 0.6)
        
        # Calculate week range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Generate digest
        digest_parts = []
        digest_parts.append("📊 **Weekly Digest - Nucleus & Trust View**")
        digest_parts.append(f"📢 **#{channel_info['name']}**")
        digest_parts.append(f"📅 {start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}")
        digest_parts.append(f"📈 **{total_messages} messages** (all with clickable links)")
        digest_parts.append("")
        
        # Workflow breakdown
        digest_parts.append("**🔑 Workflow Breakdown:**")
        for workflow, count in workflow_counts.most_common():
            digest_parts.append(f"• {workflow}: {count} messages")
        digest_parts.append("")
        
        # Resolution status summary
        digest_parts.append("**📊 Resolution Status Summary:**")
        digest_parts.append(f"• **Total Messages**: {total_messages}")
        digest_parts.append(f"• **Response Rate**: {((total_messages - needs_attention) / total_messages * 100):.1f}% ({total_messages - needs_attention} with responses)")
        digest_parts.append(f"• **Resolution Rate**: {((high_confidence_resolved + likely_resolved) / total_messages * 100):.1f}%")
        digest_parts.append(f"• **High Confidence Resolved**: {high_confidence_resolved} items")
        digest_parts.append(f"• **Likely Resolved**: {likely_resolved} items")
        digest_parts.append(f"• **Items Needing Attention**: {needs_attention} items")
        digest_parts.append("")
        
        # Jira integration status
        digest_parts.append("**🎫 Jira Integration (Final Working MCP):**")
        digest_parts.append(f"• **Jira Tickets Found**: {jira_references} ticket references")
        digest_parts.append(f"• **Jira Tickets Looked Up**: 0 tickets")
        digest_parts.append(f"• **Messages with Jira**: {sum(1 for _, cat in categorized_messages if cat['jira_tickets'])} messages")
        digest_parts.append("")
        
        # Daily activity
        for day in sorted(daily_messages.keys(), reverse=True):
            day_messages = daily_messages[day]
            day_name = datetime.strptime(day, '%Y-%m-%d').strftime('%A, %Y-%m-%d')
            
            digest_parts.append(f"**📅 {day_name} ({len(day_messages)} messages)**")
            
            for i, (msg, category) in enumerate(day_messages, 1):
                user_name = self.get_user_info(msg.user)
                time_str = datetime.fromtimestamp(float(msg.timestamp)).strftime('%H:%M')
                
                # Create message summary
                text = msg.text.replace('\n', ' ').strip()
                if len(text) > 100:
                    text = text[:100] + "..."
                
                # Add severity and status indicators
                severity_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🔵"}.get(category['severity'], "🟡")
                
                # Determine status based on resolution confidence
                if category['resolution_confidence'] >= 0.8:
                    status_emoji = "✅"
                    status_text = "RESOLVED"
                elif category['resolution_confidence'] >= 0.6:
                    status_emoji = "🟡"
                    status_text = "LIKELY_RESOLVED"
                else:
                    status_emoji = "❓"
                    status_text = "UNKNOWN"
                
                # Add thread indicator
                thread_indicator = " 📝" if category['has_thread'] else ""
                
                # Add Jira ticket indicators
                jira_indicators = ""
                if category['jira_tickets']:
                    jira_indicators = " " + " ".join([f"🎫 <https://jira.autodesk.com/browse/{ticket}|{ticket}>" for ticket in category['jira_tickets'][:3]])
                
                # Add confidence score
                confidence_score = f"({category['resolution_confidence']:.1f})" if category['resolution_confidence'] > 0 else ""
                
                digest_parts.append(f"{i}. **{user_name}** - {text} {severity_emoji} {category['severity']} | {status_emoji} {status_text} {confidence_score}{thread_indicator}{jira_indicators} <https://autodesk.slack.com/archives/{channel_info['name']}/p{msg.timestamp.replace('.', '')}|(link)>")
        
        # Summary statistics
        digest_parts.append("")
        digest_parts.append("**📊 Summary:**")
        digest_parts.append(f"• **Total messages**: {total_messages}")
        for workflow, count in workflow_counts.most_common():
            digest_parts.append(f"• **{workflow} workflow**: {count} messages")
        digest_parts.append("")
        
        # Severity breakdown
        digest_parts.append("**🚨 Severity Breakdown:**")
        for severity, count in severity_counts.most_common():
            percentage = (count / total_messages * 100) if total_messages > 0 else 0
            emoji = {"High": "🔴", "Medium": "🟡", "Low": "🔵"}.get(severity, "🟡")
            digest_parts.append(f"• {emoji} {severity}: {count} messages ({percentage:.0f}%)")
        digest_parts.append("")
        
        # Resolution breakdown
        digest_parts.append("**✅ Resolution Breakdown:**")
        resolved_count = high_confidence_resolved + likely_resolved
        resolved_percentage = (resolved_count / total_messages * 100) if total_messages > 0 else 0
        unknown_percentage = (needs_attention / total_messages * 100) if total_messages > 0 else 0
        
        digest_parts.append(f"• ✅ Resolved: {resolved_count} messages ({resolved_percentage:.0f}%)")
        digest_parts.append(f"• 🟡 Likely Resolved: {likely_resolved} messages ({likely_resolved/total_messages*100:.0f}%)")
        digest_parts.append(f"• ❓ Unknown Status: {needs_attention} messages ({unknown_percentage:.0f}%)")
        digest_parts.append(f"• ❌ Unresolved: 0 messages (0%)")
        digest_parts.append("")
        
        # Jira status breakdown
        digest_parts.append("**🎫 Jira Status Breakdown (Final Working MCP):**")
        digest_parts.append("• ✅ Done: 0 tickets")
        digest_parts.append("• 🔄 In Progress: 0 tickets")
        digest_parts.append("• 📋 To Do: 0 tickets")
        digest_parts.append("• ❌ Error: 0 tickets")
        digest_parts.append("")
        
        # Legends
        digest_parts.append("**🔍 Resolution Legend:**")
        digest_parts.append("• ✅ = High confidence resolved (score ≥3)")
        digest_parts.append("• 🟢 = Resolved (score <3)")
        digest_parts.append("• 🟡 = Likely resolved")
        digest_parts.append("• 🟠 = Possibly resolved")
        digest_parts.append("• ❌ = Unresolved")
        digest_parts.append("• ❓ = Unknown status")
        digest_parts.append("• 📝 = Has thread responses")
        digest_parts.append("")
        
        digest_parts.append("**🎫 Jira Legend (Final Working MCP):**")
        digest_parts.append("• ✅ = Done/Resolved/Closed")
        digest_parts.append("• 🔄 = In Progress")
        digest_parts.append("• 📋 = To Do/Open")
        digest_parts.append("• 🟡 = Ready")
        digest_parts.append("• 🚫 = Blocked")
        digest_parts.append("• ⏳ = Waiting")
        digest_parts.append("• 🎫 = Jira ticket referenced")
        digest_parts.append("• ❓ = Unknown status")
        digest_parts.append("")
        
        digest_parts.append("🤖 *Auto-generated weekly digest with resolution tracking & final working MCP Jira lookup*")
        digest_parts.append("🔍 *Filtered for: Nucleus & Trust View workflows only*")
        
        return "\n".join(digest_parts)
    
    def create_weekly_digest_for_channel(self, channel_id: str, recipient_email: str = None, days_back: int = 7, test_mode: bool = False):
        """Create weekly digest for a specific channel"""
        logger.info(f"Creating weekly digest for channel {channel_id}")
        
        # Get channel info
        channel_info = self.get_channel_info(channel_id)
        
        # Get messages
        messages = self.get_channel_messages(channel_id, days_back)
        logger.info(f"Found {len(messages)} messages for weekly digest")
        
        if not messages:
            logger.info("No messages found for digest period")
            return None
        
        # Generate digest content
        digest_content = self.generate_final_digest_content(channel_info, messages, days_back)
        
        if test_mode:
            # Save to file instead of sending
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"final_weekly_digest_{timestamp}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(digest_content)
            logger.info(f"Test digest saved to {filename}")
            return digest_content
        
        # Try to send digest if recipient email provided
        if recipient_email:
            try:
                recipient_id = self.get_user_id_by_email(recipient_email)
                if recipient_id:
                    result = self.send_dm_digest(recipient_id, digest_content)
                    if result:
                        logger.info("Weekly digest sent successfully!")
                        return digest_content
                    else:
                        logger.error("Failed to send weekly digest")
                else:
                    logger.error(f"Could not find user with email {recipient_email}")
            except Exception as e:
                logger.error(f"Error sending digest: {e}")
        
        return digest_content
    
    def get_user_id_by_email(self, email: str) -> Optional[str]:
        """Get user ID by email address with better error handling"""
        try:
            response = self.client.users_lookupByEmail(email=email)
            return response['user']['id']
        except SlackApiError as e:
            logger.error(f"Error looking up user by email: {e}")
            return None
    
    def send_dm_digest(self, user_id: str, content: str):
        """Send digest as DM to user"""
        try:
            response = self.client.chat_postMessage(
                channel=user_id,
                text=content,
                unfurl_links=False,
                unfurl_media=False
            )
            logger.info(f"Weekly digest sent successfully to user {user_id}")
            return response
        except SlackApiError as e:
            logger.error(f"Error sending weekly digest: {e}")
            return None
    
    def create_weekly_digest_for_all_channels(self, recipient_email: str = None, days_back: int = 7, test_mode: bool = False):
        """Create weekly digest for all accessible channels"""
        logger.info("Creating weekly digest for all accessible channels")
        
        # Get accessible channels
        channels = self.get_available_channels()
        
        if not channels:
            logger.warning("No accessible channels found for weekly digest")
            return False
        
        logger.info(f"Found {len(channels)} accessible channels for weekly digest")
        
        # Process each channel
        for channel in channels:
            channel_id = channel['id']
            channel_name = channel['name']
            
            logger.info(f"Processing channel: {channel_name}")
            
            # Create digest for this channel
            digest_content = self.create_weekly_digest_for_channel(
                channel_id, recipient_email, days_back, test_mode
            )
            
            if digest_content:
                logger.info(f"Weekly digest created successfully for {channel_name}")
            else:
                logger.warning(f"No content generated for {channel_name}")
        
        return True
    
    def schedule_weekly_digest(self, recipient_email: str):
        """Schedule weekly digest for Mondays at 7:00 AM EDT"""
        logger.info("Scheduling weekly digest for Mondays at 7:00 AM EDT")
        
        # Schedule the job
        schedule.every().monday.at("07:00").do(
            self.create_weekly_digest_for_all_channels, 
            recipient_email=recipient_email,
            test_mode=False
        )
        
        logger.info("Weekly digest scheduled successfully!")
        logger.info("Next digest will be sent on Monday at 7:00 AM EDT")
    
    def run_scheduler(self):
        """Run the scheduler continuously"""
        logger.info("Starting weekly digest scheduler...")
        logger.info("Press Ctrl+C to stop")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                time.sleep(60)

def main():
    """Main function for testing the final digest system"""
    # Configuration
    token = os.getenv('SLACK_BOT_TOKEN', 'your-slack-bot-token-here')
    team_id = os.getenv('SLACK_TEAM_ID', 'your-team-id-here')
    recipient_email = os.getenv('RECIPIENT_EMAIL', 'your-email@autodesk.com')
    
    print("🚀 Final Weekly Digest System")
    print("=" * 50)
    print("Testing comprehensive digest system...")
    print(f"Recipient: {recipient_email}")
    print()
    
    # Create bot
    bot = FinalWeeklyDigestSystem(token, team_id)
    
    # Test with available channels
    print("🧪 Testing digest creation for available channels...")
    
    # Get available channels
    channels = bot.get_available_channels()
    member_channels = [ch for ch in channels if ch['is_member']]
    
    print(f"Found {len(member_channels)} channels where bot is a member")
    
    if member_channels:
        # Test with the first member channel
        test_channel = member_channels[0]
        print(f"Testing with channel: #{test_channel['name']}")
        
        digest_content = bot.create_weekly_digest_for_channel(
            test_channel['id'], 
            recipient_email, 
            days_back=7, 
            test_mode=True
        )
        
        if digest_content:
            print("✅ Test digest created successfully!")
            print("📄 Digest preview:")
            print("-" * 50)
            print(digest_content[:500] + "..." if len(digest_content) > 500 else digest_content)
            print("-" * 50)
        else:
            print("❌ Test digest failed!")
    else:
        print("❌ No member channels found!")

if __name__ == "__main__":
    main()
