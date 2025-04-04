"""
Django settings for rage_INHP project.

Generated by 'django-admin startproject' using Django 4.2.19.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
import os
from pathlib import Path
from decouple import config

from allauth.headless.contrib import rest_framework

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-qv1=6*7#!&8gajb4@-zrh+xulqk(386vapjdcu8w$jrk)bo!9q'

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = os.environ.get('DEBUG', 'False').lower() in ['true', '1', 'yes']
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']
# ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', default='localhost').split(',')

# Sécurité HTTPS
# SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() in ['true', '1']
# SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() in ['true', '1']
# CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'True').lower() in ['true', '1']

# SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', 31536000))
# SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True').lower() in ['true', '1']
# SECURE_HSTS_PRELOAD = os.environ.get('SECURE_HSTS_PRELOAD', 'True').lower() in ['true', '1']
# X_FRAME_OPTIONS = os.environ.get('X_FRAME_OPTIONS', 'DENY')
# SECURE_BROWSER_XSS_FILTER = os.environ.get('SECURE_BROWSER_XSS_FILTER', 'True').lower() in ['true', '1']
# SECURE_CONTENT_TYPE_NOSNIFF = os.environ.get('SECURE_CONTENT_TYPE_NOSNIFF', 'True').lower() in ['true', '1']

# Logging
# LOG_FILE = os.environ.get('LOG_FILE', os.path.join(BASE_DIR, 'static/logs/django_errors.log'))
# LOG_LEVEL = os.environ.get('LOG_LEVEL', 'ERROR')

# Application definition
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'static/logs', 'django_errors.log'),  # Adjusted path
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
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.gis',
    'django.contrib.sessions',
    'django.contrib.messages',
    'rest_framework',
    'leaflet',
    'djgeojson',
    'tinymce',
    'import_export',
    'django_unicorn',
    'simple_history',
    'allauth',
    'allauth.account',
    'django.contrib.staticfiles',
    'rage',
    "phonenumber_field",
    'django_tables2',
    'django_filters',
    'crispy_forms',
    'crispy_bootstrap5',
    'django.contrib.humanize',
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
    # 'rage_INHP.middleware.RoleBasedRedirectMiddleware',
]

ROOT_URLCONF = 'rage_INHP.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'rage_INHP.context_processors.menu_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'rage_INHP.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# local one
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'rage',
        'USER': 'postgres',
        'PASSWORD': 'weddingLIFE18',
        'HOST': 'localhost',
        'PORT': '5433',
    }
}

#prod
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.contrib.gis.db.backends.postgis',  # Correct engine for GIS support
#         'NAME': os.environ.get('DATABASE_NAME'),
#         'USER': os.environ.get('DATABASE_USER'),
#         'PASSWORD': os.environ.get('DATABASE_PASSWORD'),
#         'HOST': os.environ.get('DATABASE_HOST'),
#         'PORT': os.environ.get('DATABASE_PORT'),
#     }
# }
DBBACKUP_STORAGE = 'django.rage_INHP.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': os.path.join(BASE_DIR, 'dbbackup/')}
# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
PHONENUMBER_DB_FORMAT = "NATIONAL"
PHONENUMBER_DEFAULT_FORMAT = "E164"

# Durée de vie de la session en secondes (par exemple, 30 minutes)
SESSION_COOKIE_AGE = 30 * 60  # 30 minutes

# SESSION_COOKIE_AGE = 60 * 60 * 24 * 30
# Configurer pour que la session expire uniquement après inactivité
SESSION_SAVE_EVERY_REQUEST = True  # La session sera prolongée à chaque requête
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

GDAL_LIBRARY_PATH = os.getenv('GDAL_LIBRARY_PATH', '/opt/homebrew/opt/gdal/lib/libgdal.dylib')
GEOS_LIBRARY_PATH = os.getenv('GEOS_LIBRARY_PATH', '/opt/homebrew/opt/geos/lib/libgeos_c.dylib')

LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
]

SITE_ID = 1
ACCOUNT_ADAPTER = 'rage_INHP.account_adapter.NoNewUsersAccountAdapter'

# ACCOUNT_AUTHENTICATION_METHOD = "username"
ACCOUNT_LOGIN_METHODS = {'username'}
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_SIGNUP_REDIRECT_URL = 'home'  # Redirection après l'inscription
LOGIN_REDIRECT_URL = 'home'  # Redirection après connexion
LOGOUT_REDIRECT_URL = '/accounts/login/'  # Redirection après déconnexion

USE_L10N = True

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # Authentification classique
    # `allauth` specific authentication methods, such as login by email
    'allauth.account.auth_backends.AuthenticationBackend',

)
# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (7.539989, -5.547080),  # Centre de la Côte d'Ivoire
    'DEFAULT_ZOOM': 7,  # Zoom par défaut (ajuste selon le niveau de détail souhaité)
    'MIN_ZOOM': 5,  # Zoom minimum
    'MAX_ZOOM': 18,  # Zoom maximum
    'SPATIAL_EXTENT': (-8.6, 4.3, -2.5, 10.7),  # Délimitation géographique de la Côte d'Ivoire
    'TILES': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',  # Utilisation d'OpenStreetMap
    'ATTRIBUTION': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}
AUTH_USER_MODEL = 'rage.EmployeeUser'

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
    "language": "es_ES",  # To force a specific language instead of the Django current language.
}
TINYMCE_SPELLCHECKER = True
TINYMCE_EXTRA_MEDIA = {
    'css': {
        'all': [
            ...
        ],
    },
    'js': [
        ...
    ],
}
# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'fr-FR'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# Configuration pour django-crispy-forms

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MPI_API_KEY = "a0ha3iNvhGC2qFDkcYXIODx0w6qhv3pZo9nyou2n"
