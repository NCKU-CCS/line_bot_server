# LINE BOT SERVER
---
- [Pre requirements](#prereq)
- [Setup](#setup)
- [Usage](#usage)
- [Config](#config)
- [Setup callback URL on LINE](#callback-url)

# <a name="prereq"></a> Pre requirements
- Python 3
- postgis
	- [Setup Postgis on Ubuntu](http://askubuntu.com/questions/650168/enable-postgis-extension-on-ubuntu-14-04-2)

- pygraphviz
	- [Setup pygraphviz on Ubuntu](http://www.jianshu.com/p/a3da7ecc5303)


## Install Dependency

```sh
pip install -r requirements.txt
```


# <a name="setup"></a> Setup
- [Use Different Setting Files](#setting-file)
- [Database](#db)
- [Cache](#cache)
- [Logger (Optional But Recommended)](#logger)


## <a name='setting-file'></a> Use Different Setting Files
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

## <a name='db'></a> Database
Currrently postgresql is used

### Start postgresql
```sh
pg_ctl -D /usr/local/var/postgres -l /usr/local/var/postgres/server.log start
```

## <a name='cache'></a> Cache
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
## <a name='logger'></a> Logger (Optional But Recommended)
- loggers
	- `django`: global logging
	- `dengue_linebot.DengueBotFSM`: FSM logging including all the conditional judgements and operation processes 

e.g.

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s:%(asctime)s:%(module)s:%(process)d:%(thread)d\n%(message)s'
        },
        'simple': {
            'format': '%(levelname)s\n%(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'dengue_linebot.DengueBotFSM': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    },
}
```

# <a name="usage"></a> Usage
## Run uwsgi
### Start
```sh
uwsgi --ini server-setting/linebot.ini --touch-reload=`pwd`/server-setting/linebot.ini
```

### Stop
```sh
sudo killall -s INT uwsgi
```

### View Log
```sh
sudo tail -f /var/log/bot_denguefever_daemon.log
```

# <a name="config"></a> Config
Under `denguefever_tw/dengue_linebot/dengue_bot_config`

- `FSM.json`: Finite state machine 
- `dengue_msg.json`: Static Messages


# <a name="callback-url"></a> Setup callback URL on LINE
Add **https://`Your Domain Name`/callback/** to `Webhook URL` on your LINE Developer page.

# TODO
- Setup static file path
