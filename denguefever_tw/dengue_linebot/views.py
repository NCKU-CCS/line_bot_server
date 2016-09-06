from django.http import HttpResponse, HttpResponseBadRequest
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

import logging
from pprint import pformat

import ujson
from linebot.client import LineBotClient

from .LINEBotHandler import LINE_operation_factory
from .LINEBotHandler import LINE_message_factory

client = LineBotClient(**settings.LINE_BOT_SETTINGS)
logger = logging.getLogger('django')


@csrf_exempt
def reply(request):
    # Check signature
    try:
        if not client.validate_signature(request.META['HTTP_X_LINE_CHANNELSIGNATURE'],
                                         request.body.decode('utf-8')):
            logger.warning(('Invalid request to callback function.\n'
                            'Not valid signature'
                            'request: \n {req}').format(req=request))
            return HttpResponseBadRequest()
    except KeyError as ke:
        logger.exception(('Invalid request to callback function.\n'
                          'Does not contain X-Line-Channelsignature\n'
                          'request: {req}\n'
                          'exception: {e}').format(req=request,
                                                   e=ke))
        return HttpResponseBadRequest()

    # Load request content
    req_json = ujson.loads(request.body.decode('utf-8'))
    logger.info('Request Received: {req}'.format(req=pformat(req_json, indent=4)))
    req_content = req_json['result'][0]['content']

    if 'opType' in req_content.keys():
        handler = LINE_operation_factory(client, req_content)
    elif 'contentType' in req_content.keys():
        handler = LINE_message_factory(client, req_content)
    logger.debug('{handler} is created.'.format(handler=handler.__class__.__name__))
    resp = handler.handle()
    if resp.status_code == 200:
        logger.debug(('Successfully handled\n'
                      'Response after handled:\n{resp}').format(resp=pformat(resp.text)))
    else:
        logger.debug(('Failed to handle\n'
                      'Response after handled:\n{resp}').format(resp=pformat(resp.text)))

    return HttpResponse()
