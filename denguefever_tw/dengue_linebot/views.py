from django.http import HttpResponse, HttpResponseBadRequest
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

import logging
from pprint import pformat

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage

from .DengueBotFSM import DengueBotMachine


logger = logging.getLogger('django')

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
line_parser = WebhookParser(settings.LINE_CHANNEL_SECRET)


@csrf_exempt
def reply(request):
    if request.method == 'POST':
        try:
            signature = request.META['HTTP_X_LINE_SIGNATURE']
            body = request.body.decode('utf-8')
            events = line_parser.parse(body, signature)
        except KeyError:
            logger.warning(
                'Not a LINE request.\n{req}'.format(req=pformat(request.text))
            )
            return HttpResponseBadRequest()
        except InvalidSignatureError:
            logger.warning(
                'Invalid Signature.\n{req}'.format(req=pformat(request.text))
            )
            return HttpResponseBadRequest()
        except LineBotApiError:
            logger.warning(
                'LineBotApiError.\n{req}'.format(req=pformat(request.text))
            )
            return HttpResponseBadRequest()

        for event in events:
            if isinstance(event, MessageEvent):
                resp = line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=event.message.text)
                )
        try:
            if resp.status_code == 200:
                logger.debug(('Successfully handled\n'
                              'Response after handled:\n{resp}').format(resp=pformat(resp.text)))
            else:
                logger.debug(('Failed to handle\n'
                              'Response after handled:\n{resp}').format(resp=pformat(resp.text)))
        except AttributeError:
            logger.debug('No response needed after handling.')
            return HttpResponse()
    else:
        return HttpResponseBadRequest()


@login_required
def show_fsm(request):
    DengueBotMachine.load_config()
    resp = HttpResponse(content_type="image/png")
    resp.name = 'state.png'
    machine = DengueBotMachine()
    machine.draw_graph(resp, prog='dot')
    return resp
