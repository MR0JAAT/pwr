from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'dev-key'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'rest_framework',
    'forecast',
]

MIDDLEWARE = []

ROOT_URLCONF = 'power_api.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.getenv('DJANGO_DB_PATH', str(BASE_DIR / '..' / 'data.db')),
    }
}

STATIC_URL = '/static/'
