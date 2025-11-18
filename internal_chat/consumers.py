"""
WebSocket Consumers for Internal Chat Real-Time Features
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from .models import Thread, ThreadParticipant, Message, MessageReaction
from .services import MessageService

logger = logging.getLogger(__name__)


class ThreadConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for thread-specific real-time events
    Handles: new messages, typing indicators, read receipts, reactions
    """
    
    async def connect(self):
        """
        Called when WebSocket connection is established
        """
        self.thread_id = self.scope['url_route']['kwargs']['thread_id']
        self.thread_group_name = f'thread_{self.thread_id}'
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if self.user.is_anonymous:
            await self.close(code=4001)  # Unauthorized
            return
        
        # Check if user is participant
        is_participant = await self.check_participant()
        if not is_participant:
            await self.close(code=4003)  # Forbidden
            return
        
        # Join thread group
        await self.channel_layer.group_add(
            self.thread_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection success
        await self.send(text_data=json.dumps({
            'type': 'connection.established',
            'thread_id': str(self.thread_id),
            'message': 'Connected to thread'
        }))
        
        logger.info(f"User {self.user.id} connected to thread {self.thread_id}")
    
    async def disconnect(self, close_code):
        """
        Called when WebSocket connection is closed
        """
        # Stop typing indicator if active
        await self.channel_layer.group_send(
            self.thread_group_name,
            {
                'type': 'typing_stop',
                'user_id': self.user.id,
            }
        )
        
        # Leave thread group
        await self.channel_layer.group_discard(
            self.thread_group_name,
            self.channel_name
        )
        
        logger.info(f"User {self.user.id} disconnected from thread {self.thread_id}")
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket client
        """
        try:
            data = json.loads(text_data)
            event_type = data.get('type')
            
            if event_type == 'message.send':
                await self.handle_message_send(data)
            elif event_type == 'typing.start':
                await self.handle_typing_start()
            elif event_type == 'typing.stop':
                await self.handle_typing_stop()
            elif event_type == 'message.read':
                await self.handle_message_read(data)
            elif event_type == 'reaction.add':
                await self.handle_reaction_add(data)
            elif event_type == 'reaction.remove':
                await self.handle_reaction_remove(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown event type: {event_type}'
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    # Event handlers for client requests
    async def handle_message_send(self, data):
        """Client wants to send a message"""
        content = data.get('content', '').strip()
        reply_to_id = data.get('reply_to')
        attachment_ids = data.get('attachment_ids', [])
        
        if not content:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Message content is required'
            }))
            return
        
        # Create message in database
        message = await self.create_message(content, reply_to_id, attachment_ids)
        
        if message:
            # Serialize message
            message_data = await self.serialize_message(message)
            
            logger.info(f"Broadcasting message.new to thread {self.thread_id}")
            logger.debug(f"Message data: {message_data}")
            
            # Broadcast to all participants in thread
            await self.channel_layer.group_send(
                self.thread_group_name,
                {
                    'type': 'message_new',
                    'message': message_data,
                }
            )
            
            logger.info(f"Broadcast complete for message {message.id}")
        else:
            logger.error(f"Failed to create message for user {self.user.id} in thread {self.thread_id}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to create message'
            }))
    
    async def handle_typing_start(self):
        """User started typing"""
        await self.channel_layer.group_send(
            self.thread_group_name,
            {
                'type': 'typing_start',
                'user_id': self.user.id,
                'username': self.user.username,
            }
        )
    
    async def handle_typing_stop(self):
        """User stopped typing"""
        await self.channel_layer.group_send(
            self.thread_group_name,
            {
                'type': 'typing_stop',
                'user_id': self.user.id,
            }
        )
    
    async def handle_message_read(self, data):
        """User read messages up to a certain point"""
        message_id = data.get('message_id')
        if not message_id:
            return
        
        await self.mark_messages_read(message_id)
        
        # Broadcast read receipt
        await self.channel_layer.group_send(
            self.thread_group_name,
            {
                'type': 'receipt_read',
                'user_id': self.user.id,
                'message_id': message_id,
            }
        )
    
    async def handle_reaction_add(self, data):
        """User added reaction to message"""
        message_id = data.get('message_id')
        emoji = data.get('emoji')
        
        if not message_id or not emoji:
            return
        
        # Add reaction in database
        await self.add_reaction(message_id, emoji)
        
        # Broadcast
        await self.channel_layer.group_send(
            self.thread_group_name,
            {
                'type': 'reaction_added',
                'message_id': message_id,
                'user_id': self.user.id,
                'emoji': emoji,
            }
        )
    
    async def handle_reaction_remove(self, data):
        """User removed reaction from message"""
        message_id = data.get('message_id')
        emoji = data.get('emoji')
        
        if not message_id or not emoji:
            return
        
        # Remove reaction in database
        await self.remove_reaction(message_id, emoji)
        
        # Broadcast
        await self.channel_layer.group_send(
            self.thread_group_name,
            {
                'type': 'reaction_removed',
                'message_id': message_id,
                'user_id': self.user.id,
                'emoji': emoji,
            }
        )
    
    # Channel layer event handlers (broadcast to WebSocket)
    async def message_new(self, event):
        """New message broadcast"""
        await self.send(text_data=json.dumps({
            'type': 'message.new',
            'message': event['message'],
        }))
    
    async def message_updated(self, event):
        """Message edited"""
        await self.send(text_data=json.dumps({
            'type': 'message.updated',
            'message': event['message'],
        }))
    
    async def message_deleted(self, event):
        """Message deleted"""
        await self.send(text_data=json.dumps({
            'type': 'message.deleted',
            'message_id': event['message_id'],
        }))
    
    async def typing_start(self, event):
        """Someone started typing"""
        # Don't send to self
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing.start',
                'user_id': event['user_id'],
                'username': event.get('username', ''),
            }))
    
    async def typing_stop(self, event):
        """Someone stopped typing"""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing.stop',
                'user_id': event['user_id'],
            }))
    
    async def receipt_read(self, event):
        """Read receipt"""
        await self.send(text_data=json.dumps({
            'type': 'receipt.read',
            'user_id': event['user_id'],
            'message_id': event['message_id'],
        }))
    
    async def reaction_added(self, event):
        """Reaction added"""
        await self.send(text_data=json.dumps({
            'type': 'reaction.added',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'emoji': event['emoji'],
        }))
    
    async def reaction_removed(self, event):
        """Reaction removed"""
        await self.send(text_data=json.dumps({
            'type': 'reaction.removed',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'emoji': event['emoji'],
        }))
    
    async def member_added(self, event):
        """Member added to thread"""
        await self.send(text_data=json.dumps({
            'type': 'member.added',
            'user_id': event['user_id'],
            'username': event['username'],
        }))
    
    async def member_removed(self, event):
        """Member removed from thread"""
        await self.send(text_data=json.dumps({
            'type': 'member.removed',
            'user_id': event['user_id'],
        }))
    
    async def thread_updated(self, event):
        """Thread settings/title changed"""
        await self.send(text_data=json.dumps({
            'type': 'thread.updated',
            'thread': event['thread'],
        }))
    
    async def unread_count_update(self, event):
        """Unread count update for this thread"""
        # Only send to the specific user this count is for
        if 'user_id' in event and event['user_id'] != self.user.id:
            return  # Skip sending to other users
        
        await self.send(text_data=json.dumps({
            'type': 'unread.count.update',
            'thread_id': event['thread_id'],
            'unread_count': event['unread_count'],
        }))
    
    # Database operations (async wrappers)
    @database_sync_to_async
    def check_participant(self):
        """Check if user is a participant in the thread"""
        return ThreadParticipant.objects.filter(
            thread_id=self.thread_id,
            user=self.user,
            left_at__isnull=True
        ).exists()
    
    @database_sync_to_async
    def create_message(self, content, reply_to_id, attachment_ids):
        """Create a new message"""
        try:
            return MessageService.create_message(
                thread_id=self.thread_id,
                sender=self.user,
                content=content,
                reply_to_id=reply_to_id,
                attachment_ids=attachment_ids or []
            )
        except Exception as e:
            logger.error(f"Error creating message: {str(e)}")
            return None
    
    @database_sync_to_async
    def serialize_message(self, message):
        """Serialize message to dict with user context"""
        from .serializers import MessageSerializer
        
        # Create a mock request object with current user for context
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        return MessageSerializer(message, context={'request': MockRequest(self.user)}).data
    
    @database_sync_to_async
    def mark_messages_read(self, message_id):
        """Mark messages as read up to this point"""
        try:
            thread = Thread.objects.get(id=self.thread_id)
            message = Message.objects.get(id=message_id)
            MessageService.mark_as_read(thread, self.user, message)
        except Exception as e:
            logger.error(f"Error marking messages read: {str(e)}")
    
    @database_sync_to_async
    def add_reaction(self, message_id, emoji):
        """Add reaction to message"""
        try:
            message = Message.objects.get(id=message_id, thread_id=self.thread_id)
            MessageService.add_reaction(message, self.user, emoji)
        except Exception as e:
            logger.error(f"Error adding reaction: {str(e)}")
    
    @database_sync_to_async
    def remove_reaction(self, message_id, emoji):
        """Remove reaction from message"""
        try:
            message = Message.objects.get(id=message_id, thread_id=self.thread_id)
            MessageService.remove_reaction(message, self.user, emoji)
        except Exception as e:
            logger.error(f"Error removing reaction: {str(e)}")
    
    @staticmethod
    async def send_unread_count_update(thread_id, user_id, unread_count):
        """
        Send updated unread count for a specific thread to a user
        This is a static method that can be called from services
        """
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'thread_{thread_id}',
            {
                'type': 'unread_count_update',
                'thread_id': str(thread_id),
                'unread_count': unread_count
            }
        )
        logger.debug(f"Sent unread count update for thread {thread_id} to user {user_id}: {unread_count}")


class PresenceConsumer(AsyncWebsocketConsumer):
    """
    Global presence consumer for online/offline status tracking
    """
    
    async def connect(self):
        """
        Called when WebSocket connection is established
        """
        self.user = self.scope['user']
        
        if self.user.is_anonymous:
            await self.close(code=4001)
            return
        
        self.presence_group_name = 'presence_global'
        
        # Join presence group
        await self.channel_layer.group_add(
            self.presence_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Mark user as online
        await self.set_user_online(True)
        
        # Broadcast online status
        await self.channel_layer.group_send(
            self.presence_group_name,
            {
                'type': 'user_online',
                'user_id': self.user.id,
            }
        )
        
        logger.info(f"User {self.user.id} is now online")
    
    async def disconnect(self, close_code):
        """
        Called when WebSocket connection is closed
        """
        # Mark user as offline
        await self.set_user_online(False)
        
        # Broadcast offline status
        await self.channel_layer.group_send(
            self.presence_group_name,
            {
                'type': 'user_offline',
                'user_id': self.user.id,
            }
        )
        
        # Leave presence group
        await self.channel_layer.group_discard(
            self.presence_group_name,
            self.channel_name
        )
        
        logger.info(f"User {self.user.id} is now offline")
    
    async def user_online(self, event):
        """User came online"""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user.online',
                'user_id': event['user_id'],
            }))
    
    async def user_offline(self, event):
        """User went offline"""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user.offline',
                'user_id': event['user_id'],
            }))
    
    @database_sync_to_async
    def set_user_online(self, is_online):
        """
        Update user's online status
        """
        from django.utils import timezone
        self.user.is_online = is_online
        self.user.last_seen = timezone.now()
        self.user.save(update_fields=['is_online', 'last_seen'])


class UserNotificationConsumer(AsyncWebsocketConsumer):
    """
    Global user notification WebSocket consumer
    Works across all pages for real-time updates (unread counts, notifications, etc.)
    """
    
    async def connect(self):
        """
        Called when WebSocket connection is established
        """
        self.user = self.scope['user']
        
        if self.user.is_anonymous:
            await self.close(code=4001)
            return
        
        # Join user's personal notification group
        self.group_name = f'user_{self.user.id}'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial unread counts
        await self.send_initial_unread_counts()
        
        logger.info(f"User {self.user.id} connected to notification WebSocket")
    
    async def disconnect(self, close_code):
        """
        Called when WebSocket connection is closed
        """
        # Leave user's notification group (only if it was set)
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
        
        if hasattr(self, 'user') and not self.user.is_anonymous:
            logger.info(f"User {self.user.id} disconnected from notification WebSocket")
    
    async def send_initial_unread_counts(self):
        """
        Send current unread counts when user connects
        """
        total_unread = await self.get_total_unread()
        
        await self.send(text_data=json.dumps({
            'type': 'unread.counts.initial',
            'total_unread': total_unread
        }))
    
    async def chat_unread_update(self, event):
        """
        Forward chat unread updates to user
        """
        await self.send(text_data=json.dumps({
            'type': 'chat.unread.update',
            'thread_id': event['thread_id'],
            'unread_count': event['unread_count'],
            'total_unread': event.get('total_unread')
        }))
    
    @database_sync_to_async
    def get_total_unread(self):
        """
        Get total unread count across all threads
        """
        from django.db.models import Sum
        total = ThreadParticipant.objects.filter(
            user=self.user,
            left_at__isnull=True
        ).aggregate(
            total=Sum('unread_count')
        )['total'] or 0
        return total
