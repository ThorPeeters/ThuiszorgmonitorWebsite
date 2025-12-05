from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/hartslag/', consumers.HartslagConsumer.as_asgi()),
]
