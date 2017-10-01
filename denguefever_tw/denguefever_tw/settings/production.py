from .base import *

DEBUG = False

SECRET_KEY = get_env_variable('DJANGO_SECRET_KEY')
LINE_CHANNEL_SECRET = get_env_variable('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = get_env_variable('LINE_CHANNEL_ACCESS_TOKEN')
IMGUR_CLIENT_ID = get_env_variable('IMGUR_CLIENT_ID')
CHROME_DRIVER_PATH = get_env_variable('CHROME_DRIVER_PATH')

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': get_env_variable('POSTGRESQL_NAME'),
        'USER': get_env_variable('POSTGRESQL_USER'),
        'PASSWORD': get_env_variable('POSTGRESQL_PASSWORD'),
        'HOST': get_env_variable('POSTGRESQL_HOST'),
        'PORT':  get_env_variable('POSTGRESQL_PORT'),
    },
    'tainan': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': get_env_variable('POSTGRESQL_NAME'),
        'USER': get_env_variable('POSTGRESQL_USER'),
        'PASSWORD': get_env_variable('POSTGRESQL_PASSWORD'),
        'HOST': get_env_variable('POSTGRESQL_HOST'),
        'PORT':  get_env_variable('POSTGRESQL_PORT'),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': 'localhost:6379',
    },
}
