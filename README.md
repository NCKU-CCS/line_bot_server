# Dengue Line Bot Server

Line Bot that provides information about dengue fever.  
Including the following functionality  

- Basic Dengue Fever Knowledge
- Real Time Epidemic Information
- Nearby Hospital

The main logic of this bot is based on finite state machine.  

# Clone This Project
```sh
git clone --recursive https://github.com/NCKU-CCS/line_bot_server
```

---
- [Pre Requirements](#prereq)
- [Setup](#setup)
- [Usage](#usage)
- [Configration](#config)
- [Setup callback URL on LINE](#callback-url)

# <a name="prereq"></a> Pre requirements
- Python 3
- pygraphviz (For visualizing Finite State Machine) 
    - [Setup pygraphviz on Ubuntu](http://www.jianshu.com/p/a3da7ecc5303)
- postgres (Database)

```
# mac
brew install postgresql

# ubuntu
sudo apt-get install postgresql postgresql-contrib
```
- postgis (Database)
    - [Setup Postgis on Ubuntu](http://askubuntu.com/questions/650168/enable-postgis-extension-on-ubuntu-14-04-2)
- redis (In Memeory Database)

```sh
# mac
brew install redis

# ubuntu
sudo apt-get install redis-server
```



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
All other setting files should be defined under `denguefever_tw/denguefever_tw/settings/`


Use the following command to setup or change Django settings

```sh
export DJANGO_SETTINGS_MODULE="denguefever_tw.settings.your_setting_file"
```

Change `your_setting_file` to corresponding file  
e.g. `export DJANGO_SETTINGS_MODULE="denguefever_tw.settings.production"`

### Prodcution

All the sensitive data are not versioned and should be configured by the environment variables.  
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
When developing, you should define your own `local.py` under `settings/`.  
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

SECRET_KEY = 'This is the secret key'
LINE_CHANNEL_SECRET = 'This is your Line channel secret'
LINE_CHANNEL_ACCESS_TOKEN = 'This is your Line access token'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'db_name',
        'USER': 'db_user',
        'PASSWORD': 'db_pwd',
        'HOST': 'localhost',
        'PORT': '',
    },
    'tainan': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'db_name',
        'USER': 'db_user',
        'PASSWORD': 'db_pwd',
        'HOST': 'localhost',
        'PORT': '',
    },
}
```

## <a name='db'></a> Database
Currently `postgis` is used with one `default` db and one `tainan` db.  

- `default`: Store all data other than Tainan hospital data
- `tainan`: Store Tainan hospital data

### Start postgresql
```sh
# mac
pg_ctl -D /usr/local/var/postgres -l /usr/local/var/postgres/server.log start
```

### Import Hospital Data
Import tainan hosptial data

```sh
python manage.py import_dengue_hospital
```

### Import Tainan Minimum Area Data

```sh
python manage.py import_tainan_minarea
```


## <a name='cache'></a> Cache
Cache is used to store user state.  
Currently `redis` is used  

### Start Redis
```sh
redis-server
``` 

## <a name='logger'></a> Logger (Optional But Recommended)
- loggers
    - `django`: global logging
    - `dengue_linebot.denguebot_fsm`: FSM logging including all the conditional judgements and operation processes 

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
        'dengue_linebot.denguebot_fsm': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    },
}
```

[More detail on Logging System in django](https://docs.djangoproject.com/en/1.10/topics/logging/)

# <a name="usage"></a> Usage
## Run uwsgi
### Start
```sh
sudo uwsgi --ini server-setting/linebot.ini --touch-reload=`pwd`/server-setting/linebot.ini
```

### Stop
```sh
sudo killall -s INT uwsgi
```

### Realod
```sh
touch server-setting/linebot.ini
```

### Restart 

```sh
sudo killall -s INT uwsgi
sudo uwsgi --ini server-setting/linebot.ini --touch-reload=`pwd`/server-setting/linebot.ini
```

### View Log
```sh
sudo tail -f /var/log/bot_denguefever_daemon.log
```

# <a name="config"></a> Configration
Under `denguefever_tw/denguefever_tw/static/dengue_bot_config`

- `FSM.json`: Finite state machine 
- `dengue_msg.json`: Static Messages


# <a name="callback-url"></a> Setup callback URL on LINE
Add **https://`Your Domain Name`/callback/** to `Webhook URL` on your LINE Developer page.