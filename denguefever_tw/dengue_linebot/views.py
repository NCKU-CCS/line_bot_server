from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

import logging
from datetime import datetime
from pprint import pformat

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage

from .DengueBotFSM import DengueBotMachine
from .models import MessageLog

logger = logging.getLogger('django')

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
line_parser = WebhookParser(settings.LINE_CHANNEL_SECRET)
machine = DengueBotMachine(line_bot_api)


def _log_line_api_error(e):
    logger.warning(
        ('LineBotApiError\n'
            'Status Code: {status_code}\n'
            'Error Message: {err_msg}\n'
            'Error Details: {err_detail}').format(status_code=e.status_code,
                                                  err_msg=e.error.message,
                                                  err_detail=e.error.details)
    )


@csrf_exempt
@require_POST
def reply(request):
    # Check Signature
    try:
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
        events = line_parser.parse(body, signature)
    except KeyError:
        logger.warning(
            'Not a Line request.\n{req}\n'.format(req=pformat(request.text))
        )
        return HttpResponseBadRequest()
    except InvalidSignatureError:
        logger.warning(
            'Invalid Signature.\n{req}'.format(req=pformat(request.text))
        )
        return HttpResponseBadRequest()
    except LineBotApiError as e:
        _log_line_api_error()
        return HttpResponseBadRequest()

    for event in events:
        try:
            user_id = event.source.user_id
            state = cache.get(user_id) or 'user'

            logger.info(
                ('Receive Event\n'
                 'User ID: {user_id}\n'
                 'Event Type: {event_type}\n'
                 'User state: {state}\n').format(
                     user_id=user_id,
                     event_type=event.type,
                     state=state)
            )
            content = None
            if isinstance(event, MessageEvent):
                logger.info(
                    'Message type: {message_type}\n'.format(
                        message_type=event.message.type)
                )
                if isinstance(event.message, TextMessage):
                    content = event.message.text
                    logger.info('Text: {text}\n'.format(text=content))
                message_log = MessageLog(speaker=user_id,
                                         speak_time=datetime.fromtimestamp(event.timestamp/1000),
                                         message_type=event.message.type,
                                         content=content)
                message_log.save()

            machine.set_state(state)
            advance_statue = machine.advance(event)
            cache.set(user_id, machine.state)

            logger.info(
                ('After Advance\n'
                 'Advance Status: {status}\n'
                 'User ID: {user_id}\n'
                 'Macinhe State: {m_state}\n'
                 'User State: {u_state}\n').format(
                     status=advance_statue,
                     user_id=user_id,
                     m_state=machine.state,
                     u_state=cache.get(user_id))
            )
        except LineBotApiError as e:
            _log_line_api_error(e)
            machine.reset_state()
        except Exception as e:
            logger.exception('Exception when recevie event.\n{}', str(e))
            machine.reset_state()

    return HttpResponse()


@login_required
def show_fsm(request):
    resp = HttpResponse(content_type="image/png")
    resp.name = 'state.png'
    machine.draw_graph(resp, prog='dot')
    return resp


@login_required
def reload_fsm(request):
    machine.load_config()
    return HttpResponse()
