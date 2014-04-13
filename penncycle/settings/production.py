from base import *

import dj_database_url

DEBUG = False
TEMPLATE_DEBUG = DEBUG

STATIC_URL = '/static/'

DATABASES = {
    'default': dj_database_url.config(default='postgres://localhost')
}
