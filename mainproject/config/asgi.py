import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from django.conf import settings
from alembic.config import Config
from alembic import command
import threading
import app.websocket.routing


def run_alembic_migration():
    alembic_path = os.path.join(settings.BASE_DIR, "alembic.ini")
    if os.path.exists(alembic_path):
        alembic_cfg = Config(alembic_path)
        command.upgrade(alembic_cfg, "head")
    else:
        print("Không tìm thấy alembic.ini. Bỏ qua migrations!")


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

_migration_lock = threading.Lock()
if _migration_lock.acquire(blocking=False):
    run_alembic_migration()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(app.websocket.routing.websocket_urlpatterns)
    ),
})
