from django.conf import settings

import logging
import requests
from time import sleep
from selenium import webdriver
from pyvirtualdisplay import Display

from linebot.exceptions import LineBotApiError
from linebot.models import TextSendMessage, ImageSendMessage

from .decorators import log_line_api_error

MULTICAST_LIMIT = 150
IMGUR_API_URL = 'https://api.imgur.com/3/image'
ZAPPER_MAP_URL = 'http://mosquitokiller.csie.ncku.edu.tw/zapperTown/index.html'

logger = logging.getLogger('django')


def push_msg(line_bot_api, users, text, img):
    """Push message to specific users in Line Bot.

    Use multicast of line_bot_api to push message to specific users, then
    yields the logs of push message.

    Args:
        users (List[LineUser]): users who we send message to
        text (str): the text in message
        img (str): url of the picture in message

    Yields:
        List[str]: the logs of push message to users

    Examples:
        >>> for logs in push_msg(line_bot_api=line_bot_api, users=users, text=content, img=img):
                for log in logs:
                    print(log)
        'Successfully pushed msg to XXX'
    """
    splited_users_lists = [users[i:i + MULTICAST_LIMIT]
                           for i in range(0, len(users), MULTICAST_LIMIT)]
    msgs, push_logs = list(), list()

    if text:
        msgs.append(TextSendMessage(text=text))
    if img:
        msgs.append(ImageSendMessage(original_content_url=img, preview_image_url=img))

    if msgs and splited_users_lists:
        for users in splited_users_lists:
            try:
                line_bot_api.multicast([user.user_id for user in users], msgs)
                push_logs = ["Successfully pushed msg to {user}".format(user=user)
                             for user in users]
            except LineBotApiError as error:
                log_line_api_error(error)
                push_logs = [error.error.message]
            finally:
                yield push_logs
    else:
        logger.info('Fail to push message!')


def get_web_screenshot(zapper_id):
    logger.info('Getting zapper web screenshot and uploading......\n')
    display = Display(visible=0)
    display.start()

    response = requests.get('https://mosquitokiller.csie.ncku.edu.tw/apis/lamps/{id}?key=hash'.format(
        id=zapper_id
    ))
    response_json = response.json()

    browser = webdriver.Chrome(executable_path=settings.CHROME_DRIVER_PATH)
    browser.set_window_size(1200, 900)
    browser.implicitly_wait(10)
    browser.get('{url}?lng={lng}&lat={lat}'.format(
        url=ZAPPER_MAP_URL,
        lng=response_json['lamp_location'][0],
        lat=response_json['lamp_location'][1]
    ))

    sleep(1)
    img_base64 = browser.get_screenshot_as_base64()
    browser.close()
    display.stop()

    # upload to imgur.com
    response = requests.request(
        "POST", url=IMGUR_API_URL, data=img_base64,
        headers={'authorization': 'Client-ID {client_id}'.format(client_id=settings.IMGUR_CLIENT_ID)}
    )
    response_json = response.json()

    if response.status_code == 200:
        return response_json['data']['link']
    else:
        logger.warning(
            ('ImgurApiError\n'
             'Status Code: %s\n'
             'Error Message: %s\n'),
            response.status_code, response_json['data']['error']
        )
        return False
