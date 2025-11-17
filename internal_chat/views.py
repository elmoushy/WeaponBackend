"""
API Views for Internal Chat
"""
import logging
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import CursorPagination
from django.db.models import Q, Prefetch, Sum
from django.shortcuts import get_object_or_404

from .models import (
    Thread, ThreadParticipant, Message, GroupSettings,
    Attachment, MessageReaction
)
from .serializers import (
    ThreadSerializer, ThreadCreateSerializer, ThreadUpdateSerializer,
    MessageSerializer, MessageCreateSerializer, MessageUpdateSerializer,
    ThreadParticipantSerializer, GroupSettingsSerializer,
    AttachmentSerializer, AttachmentUploadSerializer,
    AddMembersSerializer, ChangeRoleSerializer, ReactionSerializer
)
from .permissions import (
    IsThreadParticipant, IsOwnerOrAdmin,
    CanPostInThread, IsMessageSenderOrAdmin, CanChangeSettings
)
from .services import ThreadService, MessageService, ValidationService

logger = logging.getLogger(__name__)


class MessageCursorPagination(CursorPagination):
    """
    Cursor-based pagination for messages
    """
    page_size = 50
    page_size_query_param = 'limit'
    max_page_size = 100
    ordering = '-created_at'


class ThreadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for thread operations
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ThreadSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title']
    
    def get_queryset(self):
        """
        Get threads for current user with optimizations
        """
        user = self.request.user
        queryset = Thread.objects.filter(
            participants__user=user,
            participants__left_at__isnull=True
        ).distinct()
        
        # Prefetch related data for performance
        queryset = queryset.select_related('created_by')
        queryset = queryset.prefetch_related(
            Prefetch(
                'participants',
                queryset=ThreadParticipant.objects.filter(
                    left_at__isnull=True
                ).select_related('user')
            ),
            Prefetch(
                'messages',
                queryset=Message.objects.filter(
                    deleted_at__isnull=True
                ).select_related('sender').order_by('-created_at')[:1],
                to_attr='last_message_list'
            )
        )
        
        # Filter by type if requested
        thread_type = self.request.query_params.get('type')
        if thread_type in ['direct', 'group']:
            queryset = queryset.filter(type=thread_type)
        
        # Filter archived if requested
        show_archived = self.request.query_params.get('archived', 'false').lower() == 'true'
        if not show_archived:
            queryset = queryset.filter(is_archived=False)
        
        return queryset.order_by('-updated_at')
    
    def get_permissions(self):
        """
        Different permissions for different actions
        """
        if self.action == 'create':
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        elif self.action in ['retrieve', 'list']:
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def create(self, request, *args, **kwargs):
        """
        Create a new thread
        """
        serializer = ThreadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            thread = ThreadService.create_thread(
                creator=request.user,
                thread_type=serializer.validated_data['type'],
                title=serializer.validated_data.get('title'),
                participant_ids=serializer.validated_data['participant_ids']
            )
            
            output_serializer = ThreadSerializer(thread, context={'request': request})
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Error creating thread: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, *args, **kwargs):
        """
        Update thread (title, avatar)
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = ThreadUpdateSerializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        output_serializer = ThreadSerializer(instance, context={'request': request})
        return Response(output_serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """
        Archive or leave thread
        """
        thread = self.get_object()
        
        try:
            # If owner, archive thread
            participant = ThreadParticipant.objects.get(
                thread=thread,
                user=request.user,
                left_at__isnull=True
            )
            
            if participant.role == ThreadParticipant.ROLE_OWNER and thread.type == Thread.TYPE_GROUP:
                thread.is_archived = True
                thread.save()
                return Response({'message': 'Thread archived'})
            else:
                # Leave thread
                ThreadService.leave_thread(thread, request.user)
                return Response({'message': 'Left thread'})
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """
        List thread members
        """
        thread = self.get_object()
        participants = ThreadParticipant.objects.filter(
            thread=thread,
            left_at__isnull=True
        ).select_related('user')
        
        serializer = ThreadParticipantSerializer(
            participants,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwnerOrAdmin])
    def add_members(self, request, pk=None):
        """
        Add members to thread
        """
        thread = self.get_object()
        serializer = AddMembersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            added_users = ThreadService.add_participants(
                thread=thread,
                user_ids=serializer.validated_data['user_ids'],
                added_by=request.user
            )
            
            return Response({
                'message': f'Added {len(added_users)} members',
                'added_count': len(added_users)
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['delete'], url_path='members/(?P<user_id>[0-9]+)',
            permission_classes=[IsAuthenticated, IsOwnerOrAdmin])
    def remove_member(self, request, pk=None, user_id=None):
        """
        Remove member from thread
        """
        thread = self.get_object()
        
        try:
            ThreadService.remove_participant(
                thread=thread,
                user_id=user_id,
                removed_by=request.user
            )
            return Response({'message': 'Member removed'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['patch'], url_path='members/(?P<user_id>[0-9]+)/role',
            permission_classes=[IsAuthenticated, IsOwnerOrAdmin])
    def change_role(self, request, pk=None, user_id=None):
        """
        Change member role
        """
        thread = self.get_object()
        serializer = ChangeRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            ThreadService.change_participant_role(
                thread=thread,
                user_id=user_id,
                new_role=serializer.validated_data['role'],
                changed_by=request.user
            )
            return Response({'message': 'Role changed'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """
        Leave thread
        """
        thread = self.get_object()
        
        try:
            ThreadService.leave_thread(thread, request.user)
            return Response({'message': 'Left thread'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], url_path='mark-read', url_name='mark-read')
    def mark_read(self, request, pk=None):
        """
        Mark all messages in thread as read
        """
        thread = self.get_object()
        
        try:
            MessageService.mark_as_read(thread, request.user)
            return Response({'message': 'Thread marked as read'})
        except ThreadParticipant.DoesNotExist:
            return Response(
                {'error': 'You are not a participant in this thread'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error marking thread as read: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get', 'patch'], permission_classes=[IsAuthenticated, CanChangeSettings], url_path='group-settings', url_name='group-settings')
    def group_settings_action(self, request, pk=None):
        """
        Get or update thread settings
        """
        thread = self.get_object()
        
        if thread.type != Thread.TYPE_GROUP:
            return Response(
                {'error': 'Only group threads have settings'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            group_settings = thread.group_settings
        except GroupSettings.DoesNotExist:
            # Create default settings
            group_settings = GroupSettings.objects.create(thread=thread)
        
        if request.method == 'GET':
            serializer = GroupSettingsSerializer(group_settings)
            return Response(serializer.data)
        
        # PATCH - update settings
        serializer = GroupSettingsSerializer(
            group_settings,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for message operations
    """
    serializer_class = MessageSerializer
    pagination_class = MessageCursorPagination
    
    def get_queryset(self):
        """
        Get messages for a specific thread or a specific message
        """
        thread_id = self.kwargs.get('thread_id')
        
        # Base queryset with optimizations
        queryset = Message.objects.filter(
            deleted_at__isnull=True
        ).select_related('sender', 'reply_to__sender').prefetch_related(
            'attachments',
            Prefetch(
                'reactions',
                queryset=MessageReaction.objects.select_related('user')
            )
        )
        
        # Filter by thread if thread_id is provided (nested route)
        if thread_id:
            queryset = queryset.filter(thread_id=thread_id)
        else:
            # For standalone message access, filter by user's threads
            queryset = queryset.filter(
                thread__participants__user=self.request.user,
                thread__participants__left_at__isnull=True
            )
        
        queryset = queryset.order_by('-created_at')
        
        # Filter by timestamp if provided
        after = self.request.query_params.get('after')
        before = self.request.query_params.get('before')
        
        if after:
            queryset = queryset.filter(created_at__gt=after)
        if before:
            queryset = queryset.filter(created_at__lt=before)
        
        return queryset
    
    def get_permissions(self):
        """
        Different permissions for different actions
        """
        if self.action == 'create':
            return [IsAuthenticated(), CanPostInThread()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsMessageSenderOrAdmin()]
        elif self.action in ['retrieve', 'list']:
            return [IsAuthenticated(), IsThreadParticipant()]
        return super().get_permissions()
    
    def list(self, request, *args, **kwargs):
        """
        List messages in thread
        """
        thread_id = self.kwargs.get('thread_id')
        
        # Check if user is participant
        if not ThreadParticipant.objects.filter(
            thread_id=thread_id,
            user=request.user,
            left_at__isnull=True
        ).exists():
            return Response(
                {'error': 'You are not a participant in this thread'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().list(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """
        Send a new message
        """
        thread_id = self.kwargs.get('thread_id')
        thread = get_object_or_404(Thread, id=thread_id)
        
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            message = MessageService.create_message(
                thread=thread,
                sender=request.user,
                content=serializer.validated_data['content'],
                reply_to_id=serializer.validated_data.get('reply_to'),
                attachment_ids=serializer.validated_data.get('attachment_ids')
            )
            
            output_serializer = MessageSerializer(message, context={'request': request})
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Error creating message: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, *args, **kwargs):
        """
        Edit a message
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = MessageUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated_message = MessageService.update_message(
                message=instance,
                new_content=serializer.validated_data['content'],
                editor=request.user
            )
            
            output_serializer = MessageSerializer(updated_message, context={'request': request})
            return Response(output_serializer.data)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a message (soft delete)
        """
        instance = self.get_object()
        
        try:
            MessageService.delete_message(instance, request.user)
            return Response({'message': 'Message deleted'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def read(self, request, thread_id=None, pk=None):
        """
        Mark message as read
        """
        message = self.get_object()
        thread = message.thread if not thread_id else get_object_or_404(Thread, id=thread_id)
        
        try:
            MessageService.mark_as_read(thread, request.user, message)
            return Response({'message': 'Marked as read'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], url_path='react')
    def add_reaction(self, request, pk=None):
        """
        Add reaction to message
        """
        message = self.get_object()
        serializer = ReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            MessageService.add_reaction(
                message=message,
                user=request.user,
                emoji=serializer.validated_data['emoji']
            )
            # Return updated message with reactions
            output_serializer = MessageSerializer(message, context={'request': request})
            return Response(output_serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['delete'], url_path='react/(?P<emoji>[^/]+)')
    def remove_reaction(self, request, pk=None, emoji=None):
        """
        Remove reaction from message
        """
        message = self.get_object()
        
        if not emoji:
            return Response(
                {'error': 'Emoji parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            MessageService.remove_reaction(message, request.user, emoji)
            # Return updated message with reactions
            output_serializer = MessageSerializer(message, context={'request': request})
            return Response(output_serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class AttachmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for attachment operations
    """
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Get attachments for authenticated user
        """
        return Attachment.objects.filter(
            message__thread__participants__user=self.request.user,
            message__thread__participants__left_at__isnull=True
        ).distinct()
    
    def create(self, request, *args, **kwargs):
        """
        Upload an attachment
        """
        serializer = AttachmentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        attachment = serializer.save()
        
        output_serializer = AttachmentSerializer(attachment, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class UserListView(viewsets.ViewSet):
    """
    ViewSet for listing all users (for chat participant selection)
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """
        Get all active users in the system (not paginated)
        Used for dropdown/autocomplete in chat UI
        """
        from authentication.models import User
        
        # Get all active users except current user
        users = User.objects.filter(
            is_active=True
        ).exclude(
            id=request.user.id
        ).order_by('first_name', 'last_name', 'email')
        
        # Simple serialization for dropdown
        users_data = [
            {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
            }
            for user in users
        ]
        
        return Response({
            'count': len(users_data),
            'users': users_data
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_total_unread_count(request):
    """
    Get total unread message count across all threads for current user
    Used for sidebar badge
    """
    user = request.user
    
    # Sum all unread counts from user's thread participations
    total_unread = ThreadParticipant.objects.filter(
        user=user,
        left_at__isnull=True
    ).aggregate(
        total=Sum('unread_count')
    )['total'] or 0
    
    return Response({
        'total_unread_count': total_unread
    })
