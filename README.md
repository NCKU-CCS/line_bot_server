# LINE BOT SERVER

## Setup LINE API KEY
The following two methods is used to setup LINE api key.  
If the setting file doesn't exist, the environment variable are loaded.

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
Add these line to `~/.bashrc` or run these line every time you run this server.

```sh
export CHANNEL_ID=""
export CHANNEL_SECRET=""
export CHANNEL_MID=""
```

## Pre requirements
Python 3

### Install Dependency

```sh
pip install -r requirements.txt
```

## Usage

### Start
```sh
uwsgi --ini server-setting/linebot.ini --touch-reload=`pwd`/server-setting/linebot.ini
```

### Stop
```sh
sudo killall -s INT uwsgi
```

## Setup callback URL on LINE
**https://`Your Domain Name`:443/callback/** is used as `Callback URL` for LINE setting.
