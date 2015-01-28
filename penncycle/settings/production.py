from base import *


DEBUG = False
TEMPLATE_DEBUG = DEBUG


# dj_static uses STATIC_ROOT and doesn't use any STATICFILES_DIRS

INSTALLED_APPS += ('gunicorn',)

STATIC_ROOT = PROJECT_DIR.child('static')
