from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.core.cache import cache


class NotifyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print(f"[CONNECT] to {self.scope['path']}")
        self.account_id = self.scope['url_route']['kwargs']['email']
        self.group_name = f"notify_{self.account_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        print(f"[DISCONNECT] at {self.group_name}")
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            data = json.loads(text_data)
            if data["state"] == "ready":
                print(f"[CONNECTED] at {self.account_id}")
                await self.send(text_data=json.dumps({
                    "state": "connected",
                    "message": "Đã kết nối"
                }))

    async def notify_send(self, event):
        print(f"[SEND] to {self.group_name}")
        await self.send(text_data=json.dumps({
            "id": event["account_id"],
            "message": event["message"]
        }))


class TaskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print(f"[CONNECT] to {self.scope['path']}")
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.group_name = f"task_{self.task_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        print(f"[DISCONNECT] at {self.group_name}")
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            data = json.loads(text_data)
            if data["state"] == "ready":
                cache.set(f"state_{self.task_id}", True, timeout=60)
                print(f"[CONNECTED] at {self.task_id}")
                await self.send(text_data=json.dumps({
                    "state": "connected",
                    "message": "Đã kết nối"
                }))

    async def task_send(self, event):
        print(f"[SEND] to {self.group_name}")
        await self.send(text_data=json.dumps({
            "state": event["state"],
            "message": event["message"]
        }))

