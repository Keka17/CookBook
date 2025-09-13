
from pathlib import Path
import os
from django.conf.global_settings import AUTH_USER_MODEL, STATIC_ROOT
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = 'django-insecure-foo8s1=)0xr&ji4ui9-%^=(3mk!f(f(s(m@qid-s&a$f^pwh2r'


DEBUG = True


ALLOWED_HOSTS = ['127.0.0.1']

SITE_ID = 1

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'app',
    'django_ckeditor_5',
    'django_cleanup.apps.CleanupConfig',  # Для удаления файлов из media/
    'storages',
    'widget_tweaks',  # Стилизация форм
    # 'app.apps.RecipesConfig',  # Сигналы
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Django_CookBook.urls'

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

WSGI_APPLICATION = 'Django_CookBook.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Коды верификации и данные формы хранятся в кэше Redis
# Кэш Redis (db=1)
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Настройки Celery для асинхронной обработки задач
# Redis используется в качестве брокера сообщений и бэкенда для хранения результатов
# Для кэша и Celery используются разные БД с разными id
# Celery (отдельная база db=0)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Все задачи сериализуются в JSON для обеспечения совместимости
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

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


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'
MEDIA_URL = '/media/'

STATICFILES_DIRS = [
    BASE_DIR / "static"
]

MEDIA_ROOT = os.path.join(BASE_DIR, "media")


DEFAULT_FILE_STORAGE = 'Django_CookBook.s3_storage.MediaStorage'

AWS_S3_ENDPOINT_URL = 'https://storage.yandexcloud.net'

load_dotenv()
AWS_S3_ACCESS_KEY_ID = os.getenv('AWS_S3_ACCESS_KEY_ID')
AWS_S3_SECRET_ACCESS_KEY = os.getenv('AWS_S3_SECRET_ACCESS_KEY')
AWS_QUERYSTRING_AUTH = False


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'app.User'  # Кастомная модель юзера


# URL для перенаправления неаутентифицированных пользователей
# При использовании @login_required u LoginRequiredMixin
# пользователь будет перенаправлен на эту страницу для входа,
# после успешной аутентификации возвращен на запрашиваемую ранее страницу
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = '/'  # После входа переход на главную страницу


load_dotenv()

# Для разработки - вывод писем на консоль
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# productin: Почтовый мененджер для отправки кодов и ссылок
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = "smtp.gmail.com"
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
#
# EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
#
# DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
# SERVER_EMAIL = EMAIL_HOST_USER
# EMAIL_ADMIN = EMAIL_HOST_USER


CKEDITOR_5_CONFIGS = {
    "default": {
        "height": "500px",
        "language": "ru",
        "toolbar": {
            "items": [
                "heading", "|",
                "bold", "italic", "underline", "strikethrough", "|",
                "bulletedList", "numberedList", "|",
                "blockQuote", "highlight", "|",
                "undo", "redo"
            ],
            "shouldNotGroupWhenFull": True
        },
        "image": {
            "toolbar": [],  # Отключаем панель инструментов для изображений
            "upload": {"types": []}  # Запрещаем загрузку
        },
        "list": {
            "properties": {
                "styles": True,
                "startIndex": True,
                "reversed": True
            }
        }
    }
}