import os
from pathlib import Path
from decouple import config
from rage.core import version
from rage.core.version import get_version

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Secret key
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "insecure-key")

# Global apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.gis',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Auth
    'allauth',
    'allauth.account',
    # Tiers
    'rest_framework',
    'leaflet',
    'djgeojson',
    'tinymce',
    'import_export',
    'django_unicorn',
    'simple_history',
    'phonenumber_field',
    'django_tables2',
    'django_filters',
    'crispy_forms',
    'crispy_bootstrap5',
    'django.contrib.humanize',
    'rage',
    'django_celery_beat'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "allauth.account.middleware.AccountMiddleware",
    'simple_history.middleware.HistoryRequestMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'rage_INHP.middleware.PermissionDeniedRedirectMiddleware',

]

ROOT_URLCONF = 'rage_INHP.urls'

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
                # 'rage_INHP.context_processors.menu_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'rage_INHP.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'fr-FR'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
]

# Static & Media
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Leaflet
LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (7.539989, -5.547080),
    'DEFAULT_ZOOM': 7,
    'MIN_ZOOM': 5,
    'MAX_ZOOM': 18,
    'SPATIAL_EXTENT': (-8.6, 4.3, -2.5, 10.7),
    'TILES': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    'ATTRIBUTION': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}

# Tinymce
TINYMCE_JS_URL = 'https://cdn.tiny.cloud/1/no-api-key/tinymce/7/tinymce.min.js'
TINYMCE_COMPRESSOR = False
TINYMCE_DEFAULT_CONFIG = {
    "height": "320px",
    "width": "auto",
    "menubar": "file edit view insert format tools table help",
    "plugins": "advlist autolink lists link image charmap print preview anchor searchreplace visualblocks code "
               "fullscreen insertdatetime media table paste code help wordcount spellchecker",
    "toolbar": "undo redo | bold italic underline strikethrough | fontselect fontsizeselect formatselect | alignleft "
               "aligncenter alignright alignjustify | outdent indent |  numlist bullist checklist | forecolor "
               "backcolor casechange permanentpen formatpainter removeformat | pagebreak | charmap emoticons | "
               "fullscreen  preview save print | insertfile image media pageembed template link anchor codesample | "
               "a11ycheck ltr rtl | showcomments addcomment code",
    "custom_undo_redo_levels": 10,
    "language": "fr_FR",
}

# Auth
AUTH_USER_MODEL = 'rage.EmployeeUser'
SITE_ID = 1
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = '/accounts/login/'
ACCOUNT_SIGNUP_REDIRECT_URL = 'home'
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_LOGIN_METHODS = {'username'}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

APP_VERSION = get_version()
# Sessions
# SESSION_COOKIE_AGE = 60 * 60
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'static/logs', 'django_errors.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Backup DB
DBBACKUP_STORAGE = 'django.rage_INHP.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': os.path.join(BASE_DIR, 'dbbackup/')}

# Phone numbers
PHONENUMBER_DB_FORMAT = "NATIONAL"
PHONENUMBER_DEFAULT_FORMAT = "E164"
PHONENUMBER_DEFAULT_REGION = 'CI'

# Custom App Variables
CSRF_TRUSTED_ORIGINS = [
    "https://carinhp.ci",
    "http://localhost:8000",  # si développement local
    "https://www.carinhp.ci",  # si tu as aussi le www
]

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_SMS_NUMBER = os.getenv("TWILIO_SMS_NUMBER", "+14237194194")  # mets ton numéro réel ici

TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER', default='whatsapp:+14237194194')
TWILIO_CONTENT_SID = 'HXa645afca250223e0e68952c62a89a62e'
TWILIO_MESSAGING_SERVICE_SID = 'MG315cb644340b92dcb221670bbf69dbae'

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "https://graph.facebook.com/v19.0")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'


ORANGE_SMS_CLIENT_ID = config("ORANGE_SMS_CLIENT_ID")
ORANGE_SMS_CLIENT_SECRET = config("ORANGE_SMS_CLIENT_SECRET")
ORANGE_SMS_SENDER = config("ORANGE_SMS_SENDER")