"""Django settings for joulia-webserver project.
"""

import logging
import os
import socket

from raven.handlers.logging import SentryHandler
from raven.conf import setup_logging


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PRODUCTION_HOST = os.environ.get('JOULIA_PRODUCTION', 'false') == 'true'
TRAVIS = os.environ.get('TRAVIS', 'false') == 'true'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# TODO(willjschmitt): Remove this key when we go live.
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'fake-key-needs-to-be-set')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = not PRODUCTION_HOST

ALLOWED_HOSTS = [
    'joulia.io',
    'brew.joulia.io',
    'www.joulia.io',
    'example.com',
    'brew.example.com',
    '127.0.0.1',
    '[::1]',
]

# TODO(willjschmitt): SSL related settings we should enforce.
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True

# Enables cross-domain cookies for all of joulia.io.
if PRODUCTION_HOST:
    SESSION_COOKIE_DOMAIN = '.joulia.io'
    CSRF_COOKIE_DOMAIN = '.joulia.io'
else:
    SESSION_COOKIE_DOMAIN = '.example.com'
    CSRF_COOKIE_DOMAIN = '.example.com'

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'social_django',
    'rest_framework.authtoken',
    'rest_framework',
    'user',
    'brewery',
)

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'joulia.http.ConvertHTTPExceptionsMiddleware',
)

ROOT_URLCONF = 'joulia.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get(
    'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', None)
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get(
    'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', None)
SOCIAL_AUTH_GOOGLE_OAUTH2_LOGIN_REDIRECT_URL = "http://brew.joulia.io"
SOCIAL_AUTH_GOOGLE_OAUTH2_ALLOWED_REDIRECT_HOSTS = ALLOWED_HOSTS

USE_SOCIAL_AUTH_AS_ADMIN_LOGIN = True

WSGI_APPLICATION = 'joulia.wsgi.application'

LOGIN_URL = '/login/'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

if 'RDS_HOSTNAME' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ['RDS_DB_NAME'],
            'USER': os.environ['RDS_USERNAME'],
            'PASSWORD': os.environ['RDS_PASSWORD'],
            'HOST': os.environ['RDS_HOSTNAME'],
            'PORT': os.environ['RDS_PORT'],
        }
    }
elif not PRODUCTION_HOST:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'joulia',
            'USER': 'root',
            'PASSWORD': '',
            'HOST': 'localhost',
            'PORT': '3306',
        }
    }


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'EST'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATIC_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)


REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.DjangoFilterBackend',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'COERCE_DECIMAL_TO_STRING': False,
}

if not TRAVIS and PRODUCTION_HOST:
    LOGGING_DIR = "/var/log/joulia"
else:
    LOGGING_DIR = os.path.join(os.getcwd(), "log")

# Make sure the logging directory exists.
if not os.path.exists(LOGGING_DIR):
    os.makedirs(LOGGING_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(levelname)-8s %(asctime)s %(name)-12s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'filename': os.path.join(LOGGING_DIR, 'joulia.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB logfiles.
            'backupCount': 10,
        },
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': True
        },
        'requests': {
            'level': 'ERROR',
            'handlers': ['console', 'file'],
            'propagate': False
        },
    },
}

if PRODUCTION_HOST:
    sentry_dsn = os.environ['SENTRY_ADDRESS']
    handler = SentryHandler(sentry_dsn)
    handler.setLevel(logging.WARNING)
    setup_logging(handler)

    LOGGING['handlers']['sentry'] = {
        'level': 'ERROR',
        'class': 'raven.handlers.logging.SentryHandler',
        'dsn': sentry_dsn,
    }
    LOGGING['loggers']['']['handlers'].append('sentry')
