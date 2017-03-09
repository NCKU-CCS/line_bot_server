from django.contrib import auth
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.core.cache import cache
from django.shortcuts import render, render_to_response
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

import os
import logging
from datetime import datetime
from itertools import chain
from pprint import pformat

import ujson
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage

from .denguebot_fsm import generate_fsm_cls
from .models import (
    MessageLog, LineUser, Suggestion, GovReport,
    BotReplyLog, UnrecognizedMsg, ResponseToUnrecogMsg
)


logger = logging.getLogger('django')

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
line_parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

config_path = os.path.join(settings.STATIC_ROOT, 'dengue_linebot/config/')

cond_path = os.path.join(config_path, 'cond_config.json')
with open(cond_path) as cond_file:
    cond_config = ujson.load(cond_file)
FsmCls = generate_fsm_cls('ZhtwDengeuFSM', cond_config)
machine = FsmCls(line_bot_api, root_path=config_path)


def _log_line_api_error(e):
    logger.warning(
        ('LineBotApiError\n'
         'Status Code: {status_code}\n'
         'Error Message: {err_msg}\n'
         'Error Details: {err_detail}').format(status_code=e.status_code,
                                               err_msg=e.error.message,
                                               err_detail=e.error.details)
    )


def _log_received_event(event, state):
    user_id = event.source.user_id

    logger.info(
        ('Receive Event\n'
         'User ID: {user_id}\n'
         'Event Type: {event_type}\n'
         'User state: {state}\n').format(
             user_id=user_id,
             event_type=event.type,
             state=state)
    )

    if isinstance(event, MessageEvent):
        message_type = event.message.type

        logger.info('Message type: {message_type}\n'.format(message_type=message_type))
        if isinstance(event.message, TextMessage):
            content = event.message.text
            logger.info('Text: {text}\n'.format(text=content))
        else:
            content = '===This is {message_type} type message.==='.format(message_type=message_type)

        # TODO: Move datetime type casting to model
        message_log = MessageLog(speaker=LineUser.objects.get(user_id=user_id),
                                 speak_time=datetime.fromtimestamp(event.timestamp/1000),
                                 message_type=message_type,
                                 content=content)
        message_log.save()


@csrf_exempt
def login(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/')

    username = request.POST.get('username', '')
    password = request.POST.get('password', '')

    user = auth.authenticate(username=username, password=password)

    if user is not None and user.is_active:
        auth.login(request, user)
        return HttpResponseRedirect('/')
    else:
        return render_to_response('dengue_linebot/login.html')


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/login/')


@csrf_exempt
@require_POST
def reply(request):
    # Check Signature
    try:
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
        events = line_parser.parse(body, signature)
    except KeyError:
        logger.warning('Not a Line request.\n{req}\n'.format(req=pformat(request)))
        return HttpResponseBadRequest()
    except InvalidSignatureError:
        logger.warning('Invalid Signature.\n{req}'.format(req=pformat(request)))
        return HttpResponseBadRequest()
    except LineBotApiError as e:
        _log_line_api_error(e)
        return HttpResponseBadRequest()

    for event in events:
        try:
            user_id = event.source.user_id
            state = cache.get(user_id) or 'user'

            _log_received_event(event, state)

            # TODO: Change different machine
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
            logger.exception('Exception when recevie event.\n{}'.format(str(e)))
            machine.reset_state()
    return HttpResponse()


@login_required
def index(request):
    return render(request, 'dengue_linebot/index.html')


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


@login_required
def user_list(request):
    context = {'users': LineUser.objects.all()}
    return render(request, 'dengue_linebot/user_list.html', context)


@login_required
def user_detail(request, uid):
    context = {'user': LineUser.objects.get(user_id=uid)}
    return render(request, 'dengue_linebot/user_detail.html', context)


@login_required
def msg_log_list(request):
    context = {'users': LineUser.objects.all()}
    return render(request, 'dengue_linebot/msg_log_list.html', context)


@login_required
def msg_log_detail(request, uid):
    all_msg_logs = sorted(
        chain(
            MessageLog.objects.filter(speaker=uid),
            BotReplyLog.objects.filter(receiver=uid)
        ),
        key=lambda msg_log: msg_log.speak_time
    )
    context = {'all_msg_logs': all_msg_logs}
    return render(request, 'dengue_linebot/msg_log_detail.html', context)


@login_required
def unrecognized_msg_list(request):
    context = {'unrecog_msgs':  UnrecognizedMsg.objects.all()}
    return render(request, 'dengue_linebot/unrecog_msgs.html', context)


@login_required
def handle_unrecognized_msg(request, mid):
    unrecog_msg = UnrecognizedMsg.objects.get(id=mid)
    msg_content = unrecog_msg.message_log.content

    if request.method == 'POST':
        response_content = request.POST['proper_response']
        response_to_unrecog_msg = ResponseToUnrecogMsg(
            unrecognized_msg_content=msg_content,
            content=response_content
        )
        response_to_unrecog_msg.save()

        context = {'msg_content': msg_content, 'proper_response': response_content}
        return render(request, 'dengue_linebot/handle_unrecog_msg.html', context)
    else:
        try:
            response_to_unrecog_msg = ResponseToUnrecogMsg.objects.get(
                unrecognized_msg_content=msg_content
            )
            response_content = response_to_unrecog_msg.content
        except ResponseToUnrecogMsg.DoesNotExist:
            response_content = ''

        context = {'msg_content': msg_content, 'proper_response': response_content}
        return render(request, 'dengue_linebot/handle_unrecog_msg.html', context)


@login_required
def suggestion_list(request):
    context = {'suggestions': Suggestion.objects.all()}
    return render(request, 'dengue_linebot/suggestion_list.html', context)


@login_required
def gov_report_list(request):
    context = {'gov_reports': GovReport.objects.all().order_by('-report_time')}
    return render(request, 'dengue_linebot/gov_report_list.html', context)
