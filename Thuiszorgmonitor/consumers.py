import json
from channels.generic.websocket import AsyncWebsocketConsumer

class HartslagConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Voeg de client toe aan de groep
        await self.channel_layer.group_add(
            "hartslag_group",
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Verwijder de client uit de groep
        await self.channel_layer.group_discard(
            "hartslag_group",
            self.channel_name
        )

    async def receive(self, text_data):
        # Ontvangt berichten van de websocket en stuur ze door naar de groep
        data = json.loads(text_data)
        hartslag = data['hartslag']

        # Stuur het bericht naar de groep
        await self.channel_layer.group_send(
            "hartslag_group",
            {
                'type': 'hartslag_message',
                'hartslag': hartslag
            }
        )

    async def hartslag_message(self, event):
        # Stuur het bericht naar de WebSocket
        hartslag = event['hartslag']
        await self.send(text_data=json.dumps({
            'hartslag': hartslag
        }))
