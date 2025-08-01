"""
Production ASGI configuration for dr_turn project.
Optimized for WebSocket support with Redis backend.
"""

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

# Set Django settings for production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dr_turn.settings_production')
django.setup()

# Import routing after Django setup
from chatmed.routing import websocket_urlpatterns as chat_ws
from support.routing import websocket_urlpatterns as support_ws

# Combine all WebSocket URL patterns
websocket_urlpatterns = chat_ws + support_ws

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
}) 