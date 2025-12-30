import os
from alembic.config import Config
from alembic import command
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


def run_migrations():
    alembic_path = os.path.join(os.path.dirname(__file__), "alembic.ini")
    if os.path.exists(alembic_path):
        alembic_cfg = Config(alembic_path)
        command.upgrade(alembic_cfg, "head")
        print("Alembic migrations đã chạy xong!")
    else:
        print("Không tìm thấy alembic.ini. Bỏ qua migrations!")


if __name__ == '__main__':
    run_migrations()
    main()
