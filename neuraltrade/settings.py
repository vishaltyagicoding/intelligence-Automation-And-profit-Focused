"""
Django settings for NeuralTrade project.
Production-ready configuration for high-frequency trading platform.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# 🔐 NEW: CSRF trusted origins for HTTPS (fixes 403 error)
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if os.getenv('CSRF_TRUSTED_ORIGINS') else []

# Application definition
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'channels',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
    
    # Local apps
    'trading',
    'reversal_zones',
    'users',
    'payments',
    'market_data',
    'risk_management',
    'security',
    'api_docs',  # API Documentation
    'signal_alerts',  # Signal Alerts
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'payments.middleware.SubscriptionMiddleware',
]

ROOT_URLCONF = 'neuraltrade.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'neuraltrade.wsgi.application'
ASGI_APPLICATION = 'neuraltrade.asgi.application'

# Database - PostgreSQL with TimescaleDB
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'neuraltrade'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# Channels Configuration with Redis
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
            "capacity": 10000,
            "expiry": 60,
        },
    },
}

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/1')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', f'redis://{REDIS_HOST}:{REDIS_PORT}/2')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Kolkata'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_RESULT_EXTENDED = True
CELERY_RESULT_BACKEND_ALWAYS_RETRY = True
CELERY_RESULT_BACKEND_MAX_RETRIES = 10

# Celery Beat Schedule
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Cache Configuration - Using dummy cache to avoid Redis connection issues
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
}

# JWT Settings (3-day persistent login)
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=3),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# CORS Configuration
# Allow all origins since we're behind nginx proxy
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Trading Configuration
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', '')

SHOONYA_USER_ID = os.getenv('SHOONYA_USER_ID', '')
SHOONYA_PASSWORD = os.getenv('SHOONYA_PASSWORD', '')
SHOONYA_TOTP_SECRET = os.getenv('SHOONYA_TOTP_SECRET', '')
SHOONYA_VENDOR_CODE = os.getenv('SHOONYA_VENDOR_CODE', '')
SHOONYA_API_KEY = os.getenv('SHOONYA_API_KEY', '')
SHOONYA_IMEI = os.getenv('SHOONYA_IMEI', '')

# Delta Exchange Configuration
DELTA_API_KEY = os.getenv('DELTA_API_KEY', '')
DELTA_API_SECRET = os.getenv('DELTA_API_SECRET', '')

MAX_TRADES_PER_DAY = int(os.getenv('MAX_TRADES_PER_DAY', 4))
SLIPPAGE_THRESHOLD_CRYPTO = float(os.getenv('SLIPPAGE_THRESHOLD_CRYPTO', 0.0005))
SLIPPAGE_THRESHOLD_COMMODITY = float(os.getenv('SLIPPAGE_THRESHOLD_COMMODITY', 0.001))

# Redis Keys
REDIS_KEY_BINANCE_TOKEN = 'auth:binance:token'
REDIS_KEY_SHOONYA_TOKEN = 'auth:shoonya:token'
REDIS_KEY_DELTA_TOKEN = 'auth:delta:token'
REDIS_KEY_MARKET_DATA = 'market:data:{symbol}'
REDIS_KEY_ACTIVE_TRADES = 'trades:active'
REDIS_KEY_DAILY_TRADE_COUNT = 'trades:count:{date}'

# Payment Gateway Configuration (Razorpay)
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')
RAZORPAY_WEBHOOK_SECRET = os.getenv('RAZORPAY_WEBHOOK_SECRET', '')

# Pricing (in INR)
MONTHLY_PLAN_PRICE = int(os.getenv('MONTHLY_PLAN_PRICE', 499))
YEARLY_PLAN_PRICE = int(os.getenv('YEARLY_PLAN_PRICE', 4999))

# Email Configuration (Gmail SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'alberttyagi123@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')  # App password
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Security Configuration
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '')  # For API key encryption
JWT_ACCESS_TOKEN_LIFETIME = 3600  # 1 hour
JWT_REFRESH_TOKEN_LIFETIME = 86400  # 24 hours

# Kill Switch Configuration
KILL_SWITCH_LATENCY_THRESHOLD = 500  # milliseconds
KILL_SWITCH_ENABLED = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'neuraltrade.log',
            'maxBytes': 1024 * 1024 * 100,  # 100MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'trading': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# 🔒 Security Settings (Production with HTTPS)
if not DEBUG:
    # Nginx already handles SSL termination, so no need to redirect again
    SECURE_SSL_REDIRECT = False
    # Cookies must be marked secure when using HTTPS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'SAMEORIGIN'
    SECURE_HSTS_SECONDS = 0  # HSTS handled by nginx
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False

# Celery Beat: auto-calculate 30-day reversal signal history daily
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = getattr(globals().get('CELERY_BEAT_SCHEDULE') or {}, 'copy', lambda: {})()
CELERY_BEAT_SCHEDULE.update({
    'calculate-all-reversal-history-daily': {
        'task':     'reversal_zones.tasks.calculate_all_history',
        'schedule': crontab(hour=0, minute=30),
    },
    'update-all-recent-signals-every-30min': {
        'task':     'reversal_zones.tasks.update_all_recent_signals',
        'schedule': crontab(minute='*/30'),
    },
})