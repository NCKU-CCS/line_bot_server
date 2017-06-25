import logging
from datetime import datetime

from linebot.models import MessageEvent, TextMessage

from .models import MessageLog, LineUser


logger = logging.getLogger('django')


def log_line_api_error(error):
    logger.warning(
        ('LineBotApiError\n'
         'Status Code: %s\n'
         'Error Message: %s\n'
         'Error Details: %s'),
        error.status_code, error.error.message, error.error.details
    )


def log_received_event(event, state):
    user_id = event.source.user_id

    logger.info(
        ('Receive Event\n'
         'User ID: %s\n'
         'Event Type: %s\n'
         'User state: %s\n'),
        user_id, event.type, state
    )

    if isinstance(event, MessageEvent):
        message_type = event.message.type

        logger.info('Message type: %s\n', message_type)
        if isinstance(event.message, TextMessage):
            content = event.message.text
            logger.info('Text: %s\n', content)
        else:
            content = '===This is {message_type} type message.==='.format(message_type=message_type)

        message_log = MessageLog(speaker=LineUser.objects.get(user_id=user_id),
                                 speak_time=datetime.fromtimestamp(event.timestamp/1000),
                                 message_type=message_type,
                                 content=content)
        message_log.save()
