from django.urls import re_path
from . import consumer

websocket_urlpatterns = [
    re_path(r"^ws/task/(?P<task_id>[\w-]+)/$", consumer.TaskConsumer.as_asgi()),
    re_path(r"^ws/notify/(?P<email>[^/]+)/$", consumer.NotifyConsumer.as_asgi()),
]
