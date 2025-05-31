from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
import chatmed.routing

from chatmed.routing import websocket_urlpatterns as chat_ws
from support.routing import websocket_urlpatterns as about_ws

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat_ws + about_ws
        )
    ),
})
