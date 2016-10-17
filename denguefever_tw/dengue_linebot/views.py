from django.http import HttpResponse, HttpResponseBadRequest
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

import logging
from pprint import pformat

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage, FollowEvent

from .models import LineUser
from .DengueBotFSM import DengueBotMachine


logger = logging.getLogger('django')

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
line_parser = WebhookParser(settings.LINE_CHANNEL_SECRET)


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
    if request.method == 'POST':
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
                if isinstance(event, MessageEvent):
                    resp = line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=event.message.text)
                    )
                elif isinstance(event, FollowEvent):
                    user_id = event.source.user_id
                    try:
                        LineUser.objects.get(user_id)
                    except LineUser.DoesNotExist:
                        profile = line_bot_api.get_profile()
                        user = LineUser(
                            user_id=profile.user_id,
                            name=profile.display_name,
                            picture_url=profile.picture_url,
                            status_message=profile.status_message
                        )
            except LineBotApiError as e:
                _log_line_api_error()

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
