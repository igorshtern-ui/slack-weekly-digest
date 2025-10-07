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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
                if msg.get('type') == 'message':
                    # Include bot messages that contain user requests (like workflow requests)
                    # Exclude only system messages or pure bot notifications
                    text = msg.get('text', '').lower()
                    is_workflow_request = any(keyword in text for keyword in [
                        'new request from', 'request type', 'priority', 'summary', 'description'
                    ])
                    
                    if not msg.get('bot_id') or is_workflow_request:
                        # Filter for messages that came via Nucleus and TrustView automation workflows
                        text = msg.get('text', '')
                        text_lower = text.lower()
                        
                        # Look for messages that came via Nucleus or Trust View workflow automation
                        # These are typically bot messages with specific patterns
                        text = msg.get('text', '')
                        text_lower = text.lower()
                        
                        # Check if this is a Nucleus workflow automation message
                        is_nucleus_automation = False
                        if 'request type:' in text_lower:
                            # Extract the request type to check if it's specifically Nucleus
                            request_type_start = text.find('Request Type:') + len('Request Type:')
                            request_type_end = text.find('*Priority:*', request_type_start)
                            if request_type_end == -1:
                                request_type_end = text.find('*Subrequest Type:*', request_type_start)
                            if request_type_end == -1:
                                request_type_end = request_type_start + 100
                            
                            request_type = text[request_type_start:request_type_end].strip().replace('*', '').strip().lower()
                            is_nucleus_automation = 'nucleus' in request_type
                        
                        # Check if this is a Trust View workflow automation message
                        # Only include messages where Request Type is specifically "Trust View"
                        is_trustview_automation = False
                        if 'request type:' in text_lower:
                            # Extract the request type to check if it's specifically "Trust View"
                            request_type_start = text.find('Request Type:') + len('Request Type:')
                            request_type_end = text.find('*Priority:*', request_type_start)
                            if request_type_end == -1:
                                request_type_end = text.find('*Subrequest Type:*', request_type_start)
                            if request_type_end == -1:
                                request_type_end = request_type_start + 100
                            
                            request_type = text[request_type_start:request_type_end].strip().replace('*', '').strip().lower()
                            is_trustview_automation = request_type.strip() == 'trust view'
                        
                        # Debug logging
                        if is_nucleus_automation or is_trustview_automation:
                            logger.debug(f"Including message: Nucleus={is_nucleus_automation}, TrustView={is_trustview_automation}")
                        
                        if is_nucleus_automation or is_trustview_automation:
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
        
        # Determine workflow type based on Request Type (more precise)
        workflow = "Other"
        
        # Check Request Type field first (most reliable)
        if 'request type:' in text:
            request_type_start = text.find('request type:') + len('request type:')
            request_type_end = text.find('*priority:*', request_type_start)
            if request_type_end == -1:
                request_type_end = text.find('*subrequest type:*', request_type_start)
            if request_type_end == -1:
                request_type_end = request_type_start + 50
            
            request_type = text[request_type_start:request_type_end].strip().replace('*', '').strip()
            
            if 'nucleus' in request_type:
                workflow = "Nucleus"
            elif 'trust view' in request_type:
                workflow = "Trust View"
            elif 'trust dashboard' in request_type:
                workflow = "Trust View"
        else:
            # Fallback to general text search
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
        
        # Generate simplified digest
        digest_parts = []
        digest_parts.append("📊 **Weekly Digest - Nucleus & Trust View Automation**")
        digest_parts.append(f"📢 **#{channel_info['name']}** | 📅 {start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}")
        digest_parts.append(f"📈 **{total_messages} messages**")
        digest_parts.append("")
        
        # Workflow breakdown
        digest_parts.append("**🔑 Workflow Breakdown:**")
        for workflow, count in workflow_counts.most_common():
            digest_parts.append(f"• {workflow}: {count} messages")
        digest_parts.append("")
        
        # Resolution status summary (one-liner)
        resolved_count = high_confidence_resolved + likely_resolved
        digest_parts.append(f"**📊 Resolution Status:** {total_messages} total | {resolved_count} resolved | {needs_attention} need attention")
        digest_parts.append("")
        
        # Daily activity with detailed messages
        digest_parts.append("**📅 Daily Activity:**")
        for day in sorted(daily_messages.keys(), reverse=True):
            day_messages = daily_messages[day]
            day_name = datetime.strptime(day, '%Y-%m-%d').strftime('%A, %b %d')
            digest_parts.append(f"• {day_name}: {len(day_messages)} messages")
            
            # Add detailed message list for each day
            for i, (msg, category) in enumerate(day_messages, 1):
                user_name = self.get_user_info(msg.user)
                time_str = datetime.fromtimestamp(float(msg.timestamp)).strftime('%H:%M')
                
                # Extract subject/title from message
                text = msg.text.replace('\n', ' ').strip()
                subject = self._extract_subject(text)
                
                # Add severity and status indicators
                severity_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🔵"}.get(category['severity'], "🟡")
                
                # Determine status based on resolution confidence
                if category['resolution_confidence'] >= 0.8:
                    status_emoji = "✅"
                    status_text = "RESOLVED"
                elif category['resolution_confidence'] >= 0.6:
                    status_emoji = "🔄"
                    status_text = "LIKELY"
                else:
                    status_emoji = "❓"
                    status_text = "NEEDS_ATTENTION"
                
                # Add thread indicator
                thread_indicator = " 📝" if category['has_thread'] else ""
                
                # Create expanded message summary with focus on Summary field
                preview_lines = []
                
                # Extract Description field (what user actually typed)
                description_text = self._extract_description(text)
                if description_text:
                    # Split description into 2-3 lines, up to 120 characters each
                    description_words = description_text.split()
                    
                    # Create 2-3 lines with better word distribution
                    total_words = len(description_words)
                    words_per_line = max(1, total_words // 2)  # At least 1 word per line
                    
                    line1_words = description_words[:words_per_line]
                    line2_words = description_words[words_per_line:]
                    
                    # If second line is too long, split it further
                    if len(' '.join(line2_words)) > 120:
                        line2_words = description_words[words_per_line:words_per_line + words_per_line]
                        line3_words = description_words[words_per_line + words_per_line:]
                        
                        if line1_words:
                            preview_lines.append(' '.join(line1_words))
                        if line2_words:
                            preview_lines.append(' '.join(line2_words))
                        if line3_words:
                            preview_lines.append(' '.join(line3_words))
                    else:
                        if line1_words:
                            preview_lines.append(' '.join(line1_words))
                        if line2_words:
                            preview_lines.append(' '.join(line2_words))
                
                # If no summary found, fall back to general message preview
                if not preview_lines:
                    lines = text.split('\n')
                    # Take first 2 non-empty lines, up to 120 characters each
                    for line in lines[:2]:
                        line = line.strip()
                        if line:  # Skip empty lines
                            if len(line) > 120:
                                preview_lines.append(line[:120] + "...")
                            else:
                                preview_lines.append(line)
                            if len(preview_lines) >= 2:  # Limit to 2 lines
                                break
                
                # Extract actual user who made the request from message content
                actual_user = self._extract_actual_user(text)
                if actual_user:
                    user_name = self.get_user_info(actual_user)
                else:
                    user_name = self.get_user_info(msg.user)  # Fallback to message user
                
                # Format: User name with @, Type, Severity, Resolution, Request in 2-3 lines
                digest_parts.append(f"  {i}. **@{user_name}** | Type: {subject} | {severity_emoji} {category['severity']} | {status_emoji} {status_text}")
                for preview_line in preview_lines:
                    digest_parts.append(f"     {preview_line}")
        
        # Severity breakdown
        digest_parts.append("")
        digest_parts.append("**🚨 Severity:**")
        for severity, count in severity_counts.most_common():
            emoji = {"High": "🔴", "Medium": "🟡", "Low": "🔵"}.get(severity, "🟡")
            digest_parts.append(f"• {emoji} {severity}: {count}")
        
        digest_parts.append("")
        digest_parts.append("**🔍 Legends:**")
        digest_parts.append("**Severity:** 🔴 High | 🟡 Medium | 🔵 Low")
        digest_parts.append("**Resolution:** ✅ Resolved | 🔄 Likely | ❓ Needs Attention")
        digest_parts.append("**Thread:** 📝 Has responses")
        
        digest_parts.append("")
        digest_parts.append("🤖 *Auto-generated weekly digest*")
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
        
        # Send digest to Slack channel
        try:
            channel_sent = self.send_digest_to_slack_channel(digest_content, "tmp-igors-slack-digests")
            if channel_sent:
                logger.info("Weekly digest sent to #tmp-igors-slack-digests successfully!")
            else:
                logger.error("Failed to send digest to Slack channel")
        except Exception as e:
            logger.error(f"Error sending digest to channel: {e}")
        
        # Also try to send digest if recipient email provided
        if recipient_email:
            try:
                recipient_id = self.get_user_id_by_email(recipient_email)
                if recipient_id:
                    result = self.send_dm_digest(recipient_id, digest_content)
                    if result:
                        logger.info("Weekly digest also sent as DM successfully!")
                    else:
                        logger.error("Failed to send weekly digest as DM")
                else:
                    logger.error(f"Could not find user with email {recipient_email}")
            except Exception as e:
                logger.error(f"Error sending digest as DM: {e}")
        
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
    
    def send_digest_to_slack_channel(self, digest_content: str, channel_name: str = "tmp-igors-slack-digests") -> bool:
        """Send digest content to a Slack channel with one-liner + thread reply format"""
        try:
            # Use known channel ID for tmp-igors-slack-digests
            if channel_name == "tmp-igors-slack-digests":
                target_channel_id = "C09GY0TUNBS"
            else:
                # Find the channel ID for other channels
                response = self.client.conversations_list(types='public_channel,private_channel')
                channels = response.get('channels', [])
                
                target_channel_id = None
                for channel in channels:
                    if channel['name'] == channel_name:
                        target_channel_id = channel['id']
                        break
                
                if not target_channel_id:
                    logger.error(f"Channel #{channel_name} not found")
                    return False
            
            # Extract summary info for one-liner
            lines = digest_content.split('\n')
            total_messages = 0
            workflow_breakdown = {}
            severity_breakdown = {}
            
            for line in lines:
                if "**Total Messages**:" in line:
                    total_messages = int(line.split(':')[1].strip().split()[0])
                elif "• Trust View:" in line:
                    workflow_breakdown['Trust View'] = int(line.split(':')[1].strip().split()[0])
                elif "• Nucleus:" in line:
                    workflow_breakdown['Nucleus'] = int(line.split(':')[1].strip().split()[0])
                elif "• Other:" in line:
                    workflow_breakdown['Other'] = int(line.split(':')[1].strip().split()[0])
                elif "🟡 Medium:" in line:
                    severity_breakdown['Medium'] = int(line.split(':')[1].strip().split()[0])
                elif "🔴 High:" in line:
                    severity_breakdown['High'] = int(line.split(':')[1].strip().split()[0])
                elif "🔵 Low:" in line:
                    severity_breakdown['Low'] = int(line.split(':')[1].strip().split()[0])
            
                # Create simplified one-liner summary
                workflow_summary = ", ".join([f"{k}: {v}" for k, v in workflow_breakdown.items() if v > 0])
                severity_summary = ", ".join([f"{k}: {v}" for k, v in severity_breakdown.items() if v > 0])
                
                one_liner = f"📊 Weekly Digest: {total_messages} messages | {workflow_summary} | {severity_summary}"
            
            # Send one-liner as main message
            response = self.client.chat_postMessage(
                channel=target_channel_id,
                text=one_liner,
                unfurl_links=False,
                unfurl_media=False
            )
            
            if not response['ok']:
                logger.error(f"Failed to send one-liner: {response}")
                return False
            
            main_message_ts = response['ts']
            logger.info(f"One-liner sent to #{channel_name}")
            
            # Send full digest as single thread reply
            response = self.client.chat_postMessage(
                channel=target_channel_id,
                text=digest_content,
                thread_ts=main_message_ts,
                unfurl_links=False,
                unfurl_media=False
            )
            if response['ok']:
                logger.info(f"Full digest sent as single thread reply to #{channel_name}")
                return True
            else:
                logger.error(f"Failed to send thread reply: {response}")
                return False
                
        except SlackApiError as e:
            logger.error(f"Error sending digest to #{channel_name}: {e}")
            return False
    
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

    def _extract_subject(self, text: str) -> str:
        """Extract a meaningful subject/title from the message text"""
        # Look for Request Type as the main subject
        if 'Request Type:' in text:
            request_type_start = text.find('Request Type:') + len('Request Type:')
            request_type_end = text.find('*Priority:*', request_type_start)
            if request_type_end == -1:
                request_type_end = text.find('*Subrequest Type:*', request_type_start)
            if request_type_end == -1:
                request_type_end = request_type_start + 50
            
            request_type = text[request_type_start:request_type_end].strip().replace('*', '').strip()
            if request_type:
                return request_type
        
        # Look for Subrequest Type as secondary subject
        if 'Subrequest Type:' in text:
            subrequest_start = text.find('Subrequest Type:') + len('Subrequest Type:')
            subrequest_end = text.find('*Priority:*', subrequest_start)
            if subrequest_end == -1:
                subrequest_end = subrequest_start + 30
            
            subrequest_type = text[subrequest_start:subrequest_end].strip().replace('*', '').strip()
            if subrequest_type:
                return subrequest_type
        
        # Fallback to first line or first 30 characters
        first_line = text.split('\n')[0].strip()
        if len(first_line) > 30:
            return first_line[:30] + "..."
        return first_line if first_line else "No subject"

    def _extract_summary(self, text: str) -> str:
        """Extract the Summary field from the message text"""
        # Look for Summary field
        if '*Summary:*' in text:
            summary_start = text.find('*Summary:*') + len('*Summary:*')
            summary_end = text.find('*Application Name:*', summary_start)
            if summary_end == -1:
                summary_end = text.find('*Alias or Service ID:*', summary_start)
            if summary_end == -1:
                summary_end = text.find('*Division:*', summary_start)
            if summary_end == -1:
                summary_end = summary_start + 200  # Fallback to 200 chars
            
            summary = text[summary_start:summary_end].strip().replace('*', '').strip()
            if summary:
                return summary
        
        return ""

    def _extract_description(self, text: str) -> str:
        """Extract the Description field from the message text (what user actually typed)"""
        # Look for Description field
        if '*Description:*' in text:
            description_start = text.find('*Description:*') + len('*Description:*')
            description_end = text.find('*Application Name:*', description_start)
            if description_end == -1:
                description_end = text.find('*Alias or Service ID:*', description_start)
            if description_end == -1:
                description_end = text.find('*Division:*', description_start)
            if description_end == -1:
                description_end = description_start + 300  # Fallback to 300 chars for longer descriptions
            
            description = text[description_start:description_end].strip().replace('*', '').strip()
            if description:
                return description
        
        # If no Description field, fall back to Summary
        return self._extract_summary(text)

    def _extract_actual_user(self, text: str) -> str:
        """Extract the actual user who made the request from message content"""
        import re
        
        # Look for pattern: "New request from <@USER_ID> via <@BOT_ID>"
        pattern = r'New request from <@([A-Z0-9]+)> via'
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        
        # Look for any user mention in the text
        pattern = r'<@([A-Z0-9]+)>'
        matches = re.findall(pattern, text)
        if matches:
            # Return the first user mention (usually the requester)
            return matches[0]
        
        return ""

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
