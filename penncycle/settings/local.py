from base import *


DEBUG = True
TEMPLATE_DEBUG = DEBUG

STATIC_ROOT = ''  # unused locally

STATICFILES_DIRS = (
    PROJECT_DIR.child('static'),
)
