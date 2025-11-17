"""
WebSocket URL routing for Internal Chat
"""
from django.urls import path
from . import consumers


websocket_urlpatterns = [
    # Thread-specific WebSocket for real-time chat
    path('ws/internal-chat/threads/<uuid:thread_id>/', consumers.ThreadConsumer.as_asgi()),
    
    # Global presence WebSocket for online/offline status
    path('ws/internal-chat/presence/', consumers.PresenceConsumer.as_asgi()),
    
    # Global user notification WebSocket (works across all pages)
    path('ws/notifications/', consumers.UserNotificationConsumer.as_asgi()),
]
