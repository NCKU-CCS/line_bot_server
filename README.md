# LINE BOT SERVER
---

# Setup
## Use Different Setting Files
Currently tracks only `denguefever_tw/denguefever_tw/settings/productions.py`  
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

- `DJANGO_SECRET_KEY`
- `POSTGRESQL_NAME`
- `POSTGRESQL_USER`
- `POSTGRESQL_PASSWORD`
- `POSTGRESQL_HOST`
- `POSTGRESQL_PORT`

[Setup LINE API Key](#line-api-key)

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

e.g.

```python
from .base import *

SECRET_KEY = 'this is secret key'

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


[Setup LINE API Key](#line-api-key)


## <a name="line-api-key"></a>Setup LINE API Key
The following two methods is used to setup LINE api key.  
If the setting file doesn't exist, the environment variable will be loaded.

### By File
Create `denguefever_tw/denguefever_tw/.api_key.json`  
Then, enter your api information in the following format.

```json
{
    "channel_id": "",
    "channel_secret": "",
    "channel_mid": ""
}
```

### By Environment Variable
Add these line to `~/.bashrc` or run the following lines every time you run this server.

```sh
export CHANNEL_ID=""
export CHANNEL_SECRET=""
export CHANNEL_MID=""
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

# Setup callback URL on LINE
Add **https://`Your Domain Name`:443/callback/** to `Callback URL` on your LINE Developer page.
