from .base import *

DEBUG = False

SECRET_KEY = get_env_variable('SECRET_KEY')
LINE_CHANNEL_SECRET = get_env_variable('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = get_env_variable('LINE_CHANNEL_ACCESS_TOKEN')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': get_env_variable('POSTGRESQL_NAME'),
        'USER': get_env_variable('POSTGRESQL_USER'),
        'PASSWORD': get_env_variable('POSTGRESQL_PASSWORD'),
        'HOST': get_env_variable('POSTGRESQL_HOST'),
        'PORT':  get_env_variable('POSTGRESQL_PORT'),
    }
}
