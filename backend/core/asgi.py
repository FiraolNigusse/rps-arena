"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
import django
from django.core.management import call_command
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

# Auto-run migrations on startup
try:
    print("Applying migrations...")
    call_command("migrate", interactive=False)
except Exception as e:
    print(f"Migration error: {e}")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
})

