import os

from unipath import Path

import dj_database_url


ADMINS = (
    ('Razzi Abuissa', 'razzi53@gmail.com'),
    ('Marcus Pan', 'marcuspanje@gmail.com'),
    ('Peter Bryan', 'peterbbryan@gmail.com'),
    ('Brian Shi', 'brishi@seas.upenn.edu')
)

MANAGERS = ADMINS

ALLOWED_HOSTS = ['.penncycle.org', '.herokuapp.com', '.localhost']

TIME_ZONE = 'America/New_York'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = True

USE_L10N = True

USE_TZ = True

PROJECT_DIR = Path(__file__).ancestor(2)

MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: 'http://example.com/media/', 'http://media.example.com/'
MEDIA_URL = ''

STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

DATABASES = {
    'default': dj_database_url.config()
}

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'penncycle.urls'

WSGI_APPLICATION = 'wsgi.application'

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
)

TEMPLATE_DIRS = (
    PROJECT_DIR.child('templates'),
    PROJECT_DIR.child('templates').child('staff'),
    PROJECT_DIR.child('templates').child('registration'),
)

INSTALLED_APPS = (
    'app',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'mobile',
    'south',
    'staff',
    'stats',
    'storages',
    'django_twilio',
    'django_extensions',
    'crispy_forms',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'mobile.phonegap_views': {
            'handlers': ['console'],
        }
    }
}

TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
TWILIO_DEFAULT_CALLERID = 'PennCycle'

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'messenger@penncycle.org'
EMAIL_HOST_PASSWORD = os.environ['PENNCYCLE_PASSWORD']
EMAIL_PORT = 587
EMAIL_USE_TLS = True
SERVER_EMAIL = 'messenger@penncycle.org'

SEND_BROKEN_LINK_EMAILS = True

LOGIN_URL = '/admin-login/'
LOGOUT_URL = '/'
