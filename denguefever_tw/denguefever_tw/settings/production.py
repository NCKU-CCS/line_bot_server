from .base import *

DEBUG = False

SECRET_KEY = get_env_variable('DJANGO_SECRET_KEY')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': get_env_variable('POSTGRESQL_NAME'),
        'USER': get_env_variable('POSTGRESQL_USER'),
        'PASSWORD': get_env_variable('POSTGRESQL_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '',
    }
}
