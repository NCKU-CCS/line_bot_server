from datetime import datetime
from enum import IntEnum


class LINEOperationType(IntEnum):
    ADD_FRIEND = 4
    BLOCK_ACCOUNT = 8


class LINEContentType(IntEnum):
    TEXT_MSG = 1
    IMAGE_MSG = 2
    VIDEO_MSG = 3
    AUDIO_MSG = 4
    LOCATION_MSG = 7
    STICKER_MSG = 8
    CONTACT_MSG = 10


def LINE_operation_factory(client, onType):
    if onType == LINEOperationHandler.ADD_FRIEND:
        handler_cls = LINEAddFriendHandler
    elif onType == LINEOperationHandler.BLOCK_ACCOUNT:
        handler_cls == LINEBlockHandler
    else:
        raise ValueError(onType, 'No such onType')
    return handler_cls(client)


class LINEOperationHandler:
    def __init__(self, client):
        self._client = client

    def handle(self, req_content):
        self.revision = req_content['revision']
        self.op_yype = req_content['opType']
        self.params = req_content['params']


class LINEAddFriendHandler(LINEOperationHandler):
    def __init__(self, client):
        super().__init__(client)

    def handle(self, req_content):
        super().handle(req_content)
        raise NotImplementedError('Operation Currently Not Supported\n')


class LINEBlockHandler(LINEOperationHandler):
    def __init__(self, client):
        super().__init__(client)

    def handle(self, req_content):
        super().handle(req_content)
        raise NotImplementedError('Operation Currently Not Supported\n')


def LINE_message_factory(client, contentType):
    if contentType == LINEContentType.TEXT_MSG:
        handler_cls = LINETextHandler
    elif contentType == LINEContentType.IMAGE_MSG:
        handler_cls = LINEImageHandler
    elif contentType == LINEContentType.VIDEO_MSG:
        handler_cls = LINEVideoHandler
    elif contentType == LINEContentType.AUDIO_MSG:
        handler_cls = LINEAudioHandler
    elif contentType == LINEContentType.LOCATION_MSG:
        handler_cls = LINELocationHandler
    elif contentType == LINEContentType.STICKER_MSG:
        handler_cls = LINEStickerHandler
    elif contentType == LINEContentType.CONTACT_MSG:
        handler_cls = LINEContactHandler
    else:
        raise ValueError(contentType, 'No such content type')
    return handler_cls(client)


class LINEMessageHandler:
    def __init__(self, client):
        self._client = client

    def handle(self, req_content):
        self.msg_id = req_content['id']
        self.content_type = req_content['contentType']
        self.user_mid = req_content['from']
        self.created_time = datetime.fromtimestamp(
            req_content['created_time']/1000
        )
        self.to = req_content['to']
        self.to_type = req_content['toType']
        self.content_metadata = req_content['contentMetadata']
        self.text = req_content['text']
        self.location = req_content['location']

    def inform_message_not_supported(self):
        resp = self._client.send_text(
            to_mid=self.user_mid,
            text="Currently Not Support"
        )
        return resp


class LINETextHandler(LINEMessageHandler):
    def __init__(self, client):
        super().__init__(client)

    def handle(self, req_content):
        resp = self._client.send_text(
            to_mid=self.user_mid,
            text=self.text
        )
        return resp


class LINEImageHandler(LINEMessageHandler):
    def __init__(self, client):
        super().__init__(client)

    def handle(self, req_content):
        return self.inform_message_not_supported()


class LINEVideoHandler(LINEMessageHandler):
    def __init__(self, client):
        super().__init__(client)

    def handle(self, req_content):
        return self.inform_message_not_supported()


class LINEAudioHandler(LINEMessageHandler):
    def __init__(self, client):
        super().__init__(client)

    def handle(self, req_content):
        return self.inform_message_not_supported()


class LINELocationHandler(LINEMessageHandler):
    def __init__(self, client):
        super().__init__(client)

    def handle(self, req_content):
        super().handle(req_content)
        self.title = self.location['title']
        self.address = self.location['address']
        self.latitude = self.location['latitude']
        self.longitude = self.location['longitude']
        return self.inform_message_not_supported()


class LINEStickerHandler(LINEMessageHandler):
    def __init__(self, client):
        super().__init__(client)

    def handle(self, req_content):
        super().handle(req_content)
        self.STKPKGID = self.content_metadata['STKPKGID']
        self.STKID = self.content_metadata['STKID']
        self.STKVER = self.content_metadata['STKVER']
        self.STKTXT = self.content_type['STKTXT']
        return self.inform_message_not_supported()


class LINEContactHandler(LINEMessageHandler):
    def __init__(self, client):
        super().__init__(client)

    def handle(self, req_content):
        super().__init__(self, req_content)
        self.contact_mid = self.content_metadata['mid']
        self.contact_name = self.content_metadata['displayName']
        return self.inform_message_not_supported()
