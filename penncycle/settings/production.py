from base import *
from os import environ

import dj_database_url

DEBUG = False
TEMPLATE_DEBUG = DEBUG


# DATABASES = {
#     'default': dj_database_url.config(default='postgres://localhost')
# }

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
