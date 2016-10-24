# LINE BOT SERVER
---

# Setup
## Use Different Setting Files
Currently this repo tracks only `denguefever_tw/denguefever_tw/settings/productions.py`  
All other setting files should be defined under `denguefever_tw/denguefever_tw/settings`

Use the following command to setup or change django settings

```sh
export DJANGO_SETTINGS_MODULE="denguefever_tw.settings.your_setting_file"
```

Change `your_setting_file` to corresponding file  
(e.g. `denguefever_tw.settings.production`)

### Prodcution

All the sensitive data are not versioned and should be configured by environment variable.  
The variables needed including

- `DJANGO_SECRET_KEY` (loaded as `SECRET_KEY`)
- `LINE_CHANNEL_SECRET`
- `LINE_CHANNEL_ACCESS_TOKEN`
- `POSTGRESQL_NAME`
- `POSTGRESQL_USER`
- `POSTGRESQL_PASSWORD`
- `POSTGRESQL_HOST`
- `POSTGRESQL_PORT`



### Develop
When developing, you should define your own `local.py` under `settings`.  
This file will be and should be ignored by git.  

You should import `base.py` first.

```python
from .base import *
```

Then, set up the following variables

- `SECRET_KEY`
- `DATABASES`
- `LINE_CHANNEL_SECRET`
- `LINE_CHANNEL_ACCESS_TOKEN`

e.g.

```python
from .base import *

SECRET_KEY = 'This is secret key'
LINE_CHANNEL_SECRET = 'This is Line channel secret'
LINE_CHANNEL_ACCESS_TOKEN = 'This is Line access token'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'db_name',
        'USER': 'db_user',
        'PASSWORD': 'db_pwd',
        'HOST': 'localhost',
        'PORT': '',
    }
}
```

## Database
Currrently postgresql is used

### Start postgresql
```sh
pg_ctl -D /usr/local/var/postgres -l /usr/local/var/postgres/server.log start
```

## Cache
Cache is used to store user state.  

Currently database cache is used  
This lines should be added to setting file.

```python
CACHES = {
	'default': {
		'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
		'LOCATION': 'my_cache_table',
	}
}
```

After setting file is set, execute the following commad

```sh
 python manage.py createcachetable
```



# Pre requirements
Python 3

## Install Dependency

```sh
pip install -r requirements.txt
```

# Usage
## Run uwsgi
### Start
```sh
uwsgi --ini server-setting/linebot.ini --touch-reload=`pwd`/server-setting/linebot.ini
```

### Stop
```sh
sudo killall -s INT uwsgi
```

pg_ctl -D /usr/local/var/postgres -l /usr/local/var/postgres/server.log start


# Setup callback URL on LINE
Add **https://`Your Domain Name`/callback/** to `Webhook URL` on your LINE Developer page.
