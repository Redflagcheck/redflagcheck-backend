"""
WSGI config for backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""
import dotenv
dotenv.load_dotenv()
import os
from django.core.wsgi import get_wsgi_application
from django.core.handlers.wsgi import WSGIHandler

# Set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Custom WSGI Handler that bypasses host validation
class CustomWSGIHandler(WSGIHandler):
    def __init__(self):
        super().__init__()
        # Disable the host validation check
        self.check_settings = lambda: None

# Monkey patch Django's handler before getting the application
original_get_wsgi_application = get_wsgi_application

def patched_get_wsgi_application():
    from django.core.handlers import wsgi
    # Replace the WSGIHandler with our custom one
    wsgi.WSGIHandler = CustomWSGIHandler
    return original_get_wsgi_application()

application = patched_get_wsgi_application()
