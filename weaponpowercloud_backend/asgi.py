"""
ASGI config for weaponpowercloud_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weaponpowercloud_backend.settings')
django.setup()

# Import WebSocket routing and middleware after Django setup
from internal_chat.middleware import TokenAuthMiddleware
from internal_chat.routing import websocket_urlpatterns as chat_websocket_urlpatterns
from notifications.routing import websocket_urlpatterns as notification_websocket_urlpatterns

django_asgi_app = get_asgi_application()

# Combine all WebSocket URL patterns
# Notification routes first to ensure /ws/notifications/ matches correctly
all_websocket_urlpatterns = notification_websocket_urlpatterns + chat_websocket_urlpatterns

# WebSocket-enabled ASGI application - Phase 2 Real-Time Features
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        TokenAuthMiddleware(
            URLRouter(all_websocket_urlpatterns)
        )
    ),
})
