from base import *
from os import environ


DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'pcpg',
        'USER': environ.get('PC_DB_USER') or '',
        'PASSWORD': environ.get('PC_DB_PASSWORD') or '',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
