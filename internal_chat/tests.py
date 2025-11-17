"""
Comprehensive Tests for Internal Chat
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from internal_chat.models import (
    Thread, ThreadParticipant, Message, GroupSettings,
    Attachment, MessageReaction, DirectThreadKey, AuditLog
)
from internal_chat.services import ThreadService, MessageService, ValidationService

User = get_user_model()


class ThreadModelTest(TestCase):
    """Test Thread model"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1@test.com',
            email='user1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2@test.com',
            email='user2@test.com',
            password='testpass123'
        )
    
    def test_create_direct_thread(self):
        """Test creating a direct thread"""
        thread = Thread.objects.create(
            type=Thread.TYPE_DIRECT,
            created_by=self.user1
        )
        
        self.assertEqual(thread.type, Thread.TYPE_DIRECT)
        self.assertIsNone(thread.title)
        self.assertFalse(thread.is_archived)
    
    def test_create_group_thread(self):
        """Test creating a group thread"""
        thread = Thread.objects.create(
            type=Thread.TYPE_GROUP,
            title='Test Group',
            created_by=self.user1
        )
        
        self.assertEqual(thread.type, Thread.TYPE_GROUP)
        self.assertEqual(thread.title, 'Test Group')


class ThreadServiceTest(TestCase):
    """Test ThreadService business logic"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1@test.com',
            email='user1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2@test.com',
            email='user2@test.com',
            password='testpass123'
        )
    
    def test_create_direct_thread(self):
        """Test creating a direct thread via service"""
        thread = ThreadService.create_thread(
            creator=self.user1,
            thread_type=Thread.TYPE_DIRECT,
            participant_ids=[self.user2.id]
        )
        
        self.assertEqual(thread.type, Thread.TYPE_DIRECT)
        self.assertEqual(ThreadParticipant.objects.filter(thread=thread).count(), 2)
    
    def test_create_group_thread(self):
        """Test creating a group thread via service"""
        thread = ThreadService.create_thread(
            creator=self.user1,
            thread_type=Thread.TYPE_GROUP,
            title='Test Group',
            participant_ids=[self.user2.id]
        )
        
        self.assertEqual(thread.type, Thread.TYPE_GROUP)
        self.assertEqual(thread.title, 'Test Group')
        
        # Check owner role
        owner = ThreadParticipant.objects.get(thread=thread, user=self.user1)
        self.assertEqual(owner.role, ThreadParticipant.ROLE_OWNER)


class MessageServiceTest(TestCase):
    """Test MessageService business logic"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='test@test.com',
            email='test@test.com',
            password='testpass123'
        )
        self.thread = ThreadService.create_thread(
            creator=self.user,
            thread_type=Thread.TYPE_GROUP,
            title='Test',
            participant_ids=[]
        )
    
    def test_create_message(self):
        """Test creating a message"""
        message = MessageService.create_message(
            thread=self.thread,
            sender=self.user,
            content='Test message'
        )
        
        self.assertEqual(message.content, 'Test message')
        self.assertEqual(message.sender, self.user)
    
    def test_soft_delete_message(self):
        """Test soft deleting a message"""
        message = MessageService.create_message(
            thread=self.thread,
            sender=self.user,
            content='Test message'
        )
        
        MessageService.delete_message(message, self.user)
        
        message.refresh_from_db()
        self.assertIsNotNone(message.deleted_at)


class ThreadAPITest(APITestCase):
    """Test Thread API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='user1@test.com',
            email='user1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2@test.com',
            email='user2@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user1)
    
    def test_create_direct_thread(self):
        """Test creating direct thread via API"""
        url = '/api/internal-chat/threads/'
        data = {
            'type': 'direct',
            'participant_ids': [self.user2.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['type'], 'direct')
    
    def test_create_direct_thread_with_self(self):
        """Test that creating direct thread with yourself fails"""
        url = '/api/internal-chat/threads/'
        data = {
            'type': 'direct',
            'participant_ids': [self.user1.id]  # User trying to chat with themselves
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot create direct thread with yourself', response.data['error'])
    
    def test_create_group_thread(self):
        """Test creating group thread via API"""
        url = '/api/internal-chat/threads/'
        data = {
            'type': 'group',
            'title': 'Test Group',
            'participant_ids': [self.user2.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Group')
    
    def test_list_threads(self):
        """Test listing threads"""
        # Create a thread
        ThreadService.create_thread(
            creator=self.user1,
            thread_type=Thread.TYPE_GROUP,
            title='Test',
            participant_ids=[]
        )
        
        url = '/api/internal-chat/threads/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)


class MessageAPITest(APITestCase):
    """Test Message API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='test@test.com',
            email='test@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.thread = ThreadService.create_thread(
            creator=self.user,
            thread_type=Thread.TYPE_GROUP,
            title='Test',
            participant_ids=[]
        )
    
    def test_send_message(self):
        """Test sending a message via API"""
        url = f'/api/internal-chat/threads/{self.thread.id}/messages/'
        data = {
            'content': 'Test message'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Test message')
    
    def test_list_messages(self):
        """Test listing messages"""
        # Create a message
        MessageService.create_message(
            thread=self.thread,
            sender=self.user,
            content='Test message'
        )
        
        url = f'/api/internal-chat/threads/{self.thread.id}/messages/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)


class PermissionsTest(TestCase):
    """Test permission checks"""
    
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner@test.com',
            email='owner@test.com',
            password='testpass123'
        )
        self.admin = User.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='testpass123'
        )
        self.member = User.objects.create_user(
            username='member@test.com',
            email='member@test.com',
            password='testpass123'
        )
        
        self.thread = ThreadService.create_thread(
            creator=self.owner,
            thread_type=Thread.TYPE_GROUP,
            title='Test',
            participant_ids=[self.admin.id, self.member.id]
        )
        
        # Set admin role
        participant = ThreadParticipant.objects.get(thread=self.thread, user=self.admin)
        participant.role = ThreadParticipant.ROLE_ADMIN
        participant.save()
    
    def test_can_manage_members(self):
        """Test member management permissions"""
        self.assertTrue(ValidationService.can_manage_members(self.owner, self.thread))
        self.assertTrue(ValidationService.can_manage_members(self.admin, self.thread))
        self.assertFalse(ValidationService.can_manage_members(self.member, self.thread))
    
    def test_can_post_in_thread(self):
        """Test posting permissions"""
        # All mode
        self.assertTrue(ValidationService.can_post_in_thread(self.owner, self.thread))
        self.assertTrue(ValidationService.can_post_in_thread(self.member, self.thread))
        
        # Admins only mode
        settings = GroupSettings.objects.get(thread=self.thread)
        settings.posting_mode = GroupSettings.POSTING_MODE_ADMINS_ONLY
        settings.save()
        
        # Refresh thread to clear cached settings
        self.thread.refresh_from_db()
        
        self.assertTrue(ValidationService.can_post_in_thread(self.owner, self.thread))
        self.assertTrue(ValidationService.can_post_in_thread(self.admin, self.thread))
        self.assertFalse(ValidationService.can_post_in_thread(self.member, self.thread))
