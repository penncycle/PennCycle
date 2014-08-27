from base import *

import dj_database_url


DEBUG = False
TEMPLATE_DEBUG = DEBUG


DATABASES = {
    'default': dj_database_url.config()
}

# dj_static uses STATIC_ROOT and doesn't use any STATICFILES_DIRS

INSTALLED_APPS += ('gunicorn',)

STATIC_ROOT = PROJECT_DIR.child('static')
