from django.core.asgi import get_asgi_application
from configurations import importer
import os


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whosbug.config')
os.environ.setdefault("DJANGO_CONFIGURATION", "Local")
os.environ.setdefault("DJANGO_SECRET_KEY", "local")
importer.install()
application = get_asgi_application()
