from abc import ABCMeta, abstractmethod
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


class LINEBotHandler(metaclass=ABCMeta):
    def __init__(self, client, req_content):
        self._client = client
        self._load_content(req_content)

    @abstractmethod
    def _load_content(self, req_content):
        pass

    @abstractmethod
    def handle(self):
        pass


def LINE_operation_factory(client, req_content):
    op_type = req_content['opType']
    if op_type == LINEOperationType.ADD_FRIEND:
        handler_cls = LINEAddFriendHandler
    elif op_type == LINEOperationType.BLOCK_ACCOUNT:
        handler_cls == LINEBlockHandler
    else:
        raise ValueError(op_type, 'No such onType')
    return handler_cls(client, req_content)


class LINEOperationHandler(LINEBotHandler):
    def _load_content(self, req_content):
        self.revision = req_content['revision']
        self.op_type = req_content['opType']
        self.params = req_content['params']

    def handle(self):
        raise NotImplementedError('Operation Currently Not Supported\n')


class LINEAddFriendHandler(LINEOperationHandler):
    pass


class LINEBlockHandler(LINEOperationHandler):
    pass


def LINE_message_factory(client, req_content):
    content_type = req_content['contentType']
    if content_type == LINEContentType.TEXT_MSG:
        handler_cls = LINETextHandler
    elif content_type == LINEContentType.IMAGE_MSG:
        handler_cls = LINEImageHandler
    elif content_type == LINEContentType.VIDEO_MSG:
        handler_cls = LINEVideoHandler
    elif content_type == LINEContentType.AUDIO_MSG:
        handler_cls = LINEAudioHandler
    elif content_type == LINEContentType.LOCATION_MSG:
        handler_cls = LINELocationHandler
    elif content_type == LINEContentType.STICKER_MSG:
        handler_cls = LINEStickerHandler
    elif content_type == LINEContentType.CONTACT_MSG:
        handler_cls = LINEContactHandler
    else:
        raise ValueError(content_type, 'No such content type')
    return handler_cls(client, req_content)


class LINEMessageHandler(LINEBotHandler):
    def _load_content(self, req_content):
        self.msg_id = req_content['id']
        self.content_type = req_content['contentType']
        self.user_mid = req_content['from']
        self.created_time = datetime.fromtimestamp(
            req_content['createdTime']/1000
        )
        self.to = req_content['to']
        self.to_type = req_content['toType']
        self.content_metadata = req_content['contentMetadata']
        self.text = req_content['text']
        self.location = req_content['location']

    def handle(self):
        return self.inform_message_not_supported()

    def inform_message_not_supported(self):
        resp = self._client.send_text(
            to_mid=self.user_mid,
            text="Currently Not Support"
        )
        return resp


class LINETextHandler(LINEMessageHandler):
    def handle(self):
        resp = self._client.send_text(
            to_mid=self.user_mid,
            text=self.text
        )
        return resp


class LINEImageHandler(LINEMessageHandler):
    pass


class LINEVideoHandler(LINEMessageHandler):
    pass


class LINEAudioHandler(LINEMessageHandler):
    pass


class LINELocationHandler(LINEMessageHandler):
    def _load_content(self, req_content):
        super()._load_content(req_content)
        self.title = self.location['title']
        self.address = self.location['address']
        self.latitude = self.location['latitude']
        self.longitude = self.location['longitude']

    def handle(self):
        resp = self._client.send_location(
            to_mid=self.user_mid,
            title='Location',
            address=self.address,
            latitude=self.latitude,
            longitude=self.longitude,
        )
        return resp


class LINEStickerHandler(LINEMessageHandler):
    def _load_content(self, req_content):
        super()._load_content(req_content)
        self.STKPKGID = self.content_metadata['STKPKGID']
        self.STKID = self.content_metadata['STKID']
        self.STKVER = self.content_metadata['STKVER']
        self.STKTXT = self.content_metadata['STKTXT']


class LINEContactHandler(LINEMessageHandler):
    def _load_content(self, req_content):
        super()._load_content(req_content)
        self.contact_mid = self.content_metadata['mid']
        self.contact_name = self.content_metadata['displayName']
