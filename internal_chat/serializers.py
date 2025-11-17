"""
DRF Serializers for Internal Chat
"""
from rest_framework import serializers
from django.conf import settings
from authentication.models import User
from .models import (
    Thread, ThreadParticipant, Message, GroupSettings,
    Attachment, MessageReaction, AuditLog
)
from .services import ThreadService


class UserBasicSerializer(serializers.ModelSerializer):
    """
    Basic user info for chat participants
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = fields


class MessageReactionSerializer(serializers.ModelSerializer):
    """
    Serializer for message reactions
    """
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = MessageReaction
        fields = ['id', 'emoji', 'user', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class AttachmentSerializer(serializers.ModelSerializer):
    """
    Serializer for message attachments
    """
    url = serializers.SerializerMethodField()
    size_mb = serializers.ReadOnlyField()
    
    class Meta:
        model = Attachment
        fields = ['id', 'file_name', 'content_type', 'size', 'size_mb', 'url', 'created_at']
        read_only_fields = ['id', 'size', 'size_mb', 'created_at']
    
    def get_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class AttachmentUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading attachments
    """
    file = serializers.FileField()
    
    class Meta:
        model = Attachment
        fields = ['id', 'file', 'file_name', 'content_type', 'size']
        read_only_fields = ['id', 'size', 'content_type']
    
    def validate_file(self, value):
        # Check file size
        max_size = getattr(settings, 'INTERNAL_CHAT_MAX_ATTACHMENT_SIZE', 10 * 1024 * 1024)
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size exceeds maximum allowed size of {max_size / (1024 * 1024)}MB"
            )
        
        # Check content type
        allowed_types = getattr(settings, 'INTERNAL_CHAT_ALLOWED_CONTENT_TYPES', [])
        if allowed_types and value.content_type not in allowed_types:
            raise serializers.ValidationError(
                f"File type {value.content_type} is not allowed"
            )
        
        return value
    
    def create(self, validated_data):
        file = validated_data['file']
        
        # Create attachment without message (will be linked later)
        attachment = Attachment.objects.create(
            message=None,  # Will be set when message is created
            file=file,
            file_name=validated_data.get('file_name', file.name),
            content_type=file.content_type,
            size=file.size
        )
        
        return attachment


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for messages (list and detail)
    """
    sender = UserBasicSerializer(read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)
    reply_to = serializers.SerializerMethodField()
    is_edited = serializers.SerializerMethodField()
    is_deleted = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    thread_id = serializers.UUIDField(source='thread.id', read_only=True)
    updated_at = serializers.DateTimeField(source='edited_at', read_only=True, allow_null=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'thread_id', 'sender', 'content', 'reply_to',
            'has_attachments', 'attachments', 'reactions',
            'is_edited', 'is_deleted', 'is_read',
            'created_at', 'updated_at', 'edited_at'
        ]
        read_only_fields = [
            'id', 'thread_id', 'sender', 'has_attachments',
            'is_edited', 'is_deleted', 'is_read',
            'created_at', 'updated_at', 'edited_at'
        ]
    
    def get_reply_to(self, obj):
        if obj.reply_to and not obj.reply_to.is_deleted():
            return {
                'id': obj.reply_to.id,
                'content': obj.reply_to.content[:100],
                'sender': UserBasicSerializer(obj.reply_to.sender).data
            }
        return None
    
    def get_is_edited(self, obj):
        return obj.edited_at is not None
    
    def get_is_deleted(self, obj):
        return obj.deleted_at is not None
    
    def get_is_read(self, obj):
        """
        Check if current user has read this message.
        Returns False if no user in context (for WebSocket broadcasts).
        """
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            # For WebSocket messages, default to False
            # The frontend will update read status separately
            return False
        
        user = request.user
        if not user or user.is_anonymous:
            return False
        
        # Check if user has read up to this message
        try:
            participant = ThreadParticipant.objects.get(
                thread=obj.thread,
                user=user,
                left_at__isnull=True
            )
            if participant.last_read_at:
                return obj.created_at <= participant.last_read_at
            return False
        except ThreadParticipant.DoesNotExist:
            return False


class MessageCreateSerializer(serializers.Serializer):
    """
    Serializer for creating messages
    """
    content = serializers.CharField(max_length=10000)
    reply_to = serializers.UUIDField(required=False, allow_null=True)
    attachment_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    
    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Message content cannot be empty")
        return value.strip()


class MessageUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating messages
    """
    content = serializers.CharField(max_length=10000)
    
    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Message content cannot be empty")
        return value.strip()


class ThreadParticipantSerializer(serializers.ModelSerializer):
    """
    Serializer for thread participants
    """
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = ThreadParticipant
        fields = [
            'id', 'user', 'role', 'is_muted', 'last_read_at',
            'joined_at', 'unread_count'
        ]
        read_only_fields = ['id', 'user', 'joined_at', 'unread_count']


class GroupSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for group settings
    """
    class Meta:
        model = GroupSettings
        fields = [
            'id', 'posting_mode', 'mentions_enabled',
            'reactions_enabled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ThreadSerializer(serializers.ModelSerializer):
    """
    Serializer for threads (list and detail)
    """
    created_by = UserBasicSerializer(read_only=True)
    chat_name = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    participant_count = serializers.ReadOnlyField()
    my_role = serializers.SerializerMethodField()
    participants = ThreadParticipantSerializer(many=True, read_only=True)
    group_settings = GroupSettingsSerializer(read_only=True)
    
    class Meta:
        model = Thread
        fields = [
            'id', 'type', 'title', 'avatar', 'is_archived',
            'created_by', 'chat_name', 'last_message', 'unread_count',
            'participant_count', 'my_role', 'participants',
            'group_settings', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'type', 'created_by', 'chat_name', 'last_message',
            'unread_count', 'participant_count', 'my_role',
            'created_at', 'updated_at'
        ]
    
    def get_last_message(self, obj):
        # Get from prefetched last_message_list if available
        if hasattr(obj, 'last_message_list') and obj.last_message_list:
            message = obj.last_message_list[0]
            return {
                'id': message.id,
                'sender': UserBasicSerializer(message.sender).data,
                'content': message.content[:100],
                'created_at': message.created_at
            }
        
        # Fallback query
        last_msg = obj.messages.filter(deleted_at__isnull=True).order_by('-created_at').first()
        if last_msg:
            return {
                'id': last_msg.id,
                'sender': UserBasicSerializer(last_msg.sender).data,
                'content': last_msg.content[:100],
                'created_at': last_msg.created_at
            }
        return None
    
    def get_unread_count(self, obj):
        """
        Get unread count for current user from stored field
        """
        user = self.context['request'].user
        try:
            participant = ThreadParticipant.objects.get(
                thread=obj,
                user=user,
                left_at__isnull=True
            )
            return participant.unread_count
        except ThreadParticipant.DoesNotExist:
            return 0
    
    def get_my_role(self, obj):
        user = self.context['request'].user
        try:
            participant = obj.participants.get(user=user, left_at__isnull=True)
            return participant.role
        except ThreadParticipant.DoesNotExist:
            return None
    
    def get_chat_name(self, obj):
        """
        Get display name for the chat:
        - For group chats: return the group title
        - For direct chats: return the other person's full name
        """
        if obj.type == Thread.TYPE_GROUP:
            # For group chats, return the title
            return obj.title
        
        elif obj.type == Thread.TYPE_DIRECT:
            # For direct chats, return the other participant's name
            user = self.context['request'].user
            
            # Get the other participant (not the current user)
            other_participant = obj.participants.filter(
                left_at__isnull=True
            ).exclude(user=user).select_related('user').first()
            
            if other_participant:
                other_user = other_participant.user
                # Return full name if available, otherwise email
                if other_user.first_name or other_user.last_name:
                    return f"{other_user.first_name} {other_user.last_name}".strip()
                return other_user.email
            
            return "Unknown User"
        
        return None


class ThreadCreateSerializer(serializers.Serializer):
    """
    Serializer for creating threads
    """
    type = serializers.ChoiceField(choices=['direct', 'group'])
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    
    def validate(self, data):
        if data['type'] == 'direct':
            if len(data['participant_ids']) != 1:
                raise serializers.ValidationError({
                    'participant_ids': "Direct thread must have exactly 1 other participant"
                })
        elif data['type'] == 'group':
            if not data.get('title'):
                raise serializers.ValidationError({
                    'title': "Group thread must have a title"
                })
        
        return data


class ThreadUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating threads
    """
    class Meta:
        model = Thread
        fields = ['title', 'avatar']


class AddMembersSerializer(serializers.Serializer):
    """
    Serializer for adding members to thread
    """
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )


class ChangeRoleSerializer(serializers.Serializer):
    """
    Serializer for changing member role
    """
    role = serializers.ChoiceField(choices=['admin', 'member'])


class ReactionSerializer(serializers.Serializer):
    """
    Serializer for adding reactions
    """
    emoji = serializers.CharField(max_length=10)
    
    def validate_emoji(self, value):
        # Basic emoji validation
        if not value or len(value) > 10:
            raise serializers.ValidationError("Invalid emoji")
        return value


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for audit logs
    """
    actor = UserBasicSerializer(read_only=True)
    target_user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'actor', 'action', 'thread', 'target_user',
            'metadata', 'created_at'
        ]
        read_only_fields = fields
