import logging

from linebot.exceptions import LineBotApiError
from linebot.models import TextSendMessage, ImageSendMessage

from .decorators import log_line_api_error


MULTICAST_LIMIT = 150

logger = logging.getLogger('django')


def push_msg(line_bot_api, users, text, img):
    """Push message to specific users in Line Bot

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
