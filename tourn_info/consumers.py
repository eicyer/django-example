# yourapp/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from tourn_info.signals import one_button_clicked

class WebSocketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

        # Connect to the button_status_changed signal
        one_button_clicked.connect(self.send_button_status_changed_signal)

    async def disconnect(self, close_code):
        # Disconnect from the signal when the WebSocket is closed
        one_button_clicked.disconnect(self.send_button_status_changed_signal)

    async def send_button_status_changed_signal(self, event):
        await self.send(text_data=json.dumps({'signal': 'button_status_changed'}))

