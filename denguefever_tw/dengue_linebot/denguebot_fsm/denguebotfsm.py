import logging
import os
from datetime import datetime
from functools import wraps, partial
from urllib.parse import parse_qs

import ujson
from geopy.geocoders import GoogleV3
from condconf import CondMeta, cond_func_generator
from linebot.models import (
    MessageEvent, FollowEvent, UnfollowEvent, JoinEvent, LeaveEvent,
    PostbackEvent, BeaconEvent,
    TextMessage, StickerMessage, LocationMessage,
    ImageMessage, VideoMessage, AudioMessage,
    TextSendMessage, ImageSendMessage, LocationSendMessage,
    TemplateSendMessage, CarouselTemplate,
    CarouselColumn, MessageTemplateAction, URITemplateAction,
    ButtonsTemplate, PostbackTemplateAction
)

import hospital
from ..models import (
    LineUser, Suggestion, GovReport,
    UnrecognizedMsg, MessageLog, BotReplyLog, ResponseToUnrecogMsg
)
from .botfsm import BotGraphMachine


logger = logging.getLogger(__name__)


def log_fsm_condition(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        logger.info(
            '{condition} is {result}\n'.format(
                condition=func.__name__,
                result=result)
        )
        return result
    return wrapper


def log_fsm_operation(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        pre_state = self.state
        result = func(self, *args, **kwargs)
        post_state = self.state
        logger.info(
            ('FSM Opertion\n'
             'Beforce Advance: {pre_state}\n'
             'Triggered Function: {func}\n'
             'After Advance: {post_state}\n').format(
                 pre_state=pre_state,
                 func=func.__name__,
                 post_state=post_state)
        )
        return result
    return wrapper


class LineBotEventConditionMixin:
    def _assert_message_type(self, event, event_type):
        return isinstance(event, MessageEvent) and isinstance(event.message, event_type)

    @log_fsm_condition
    def is_text_message(self, event):
        return self._assert_message_type(event, TextMessage)

    @log_fsm_condition
    def is_sticker_message(self, event):
        return self._assert_message_type(event, StickerMessage)

    @log_fsm_condition
    def is_image_message(self, event):
        return self._assert_message_type(event, ImageMessage)

    @log_fsm_condition
    def is_video_message(self, event):
        return self._assert_message_type(event, VideoMessage)

    @log_fsm_condition
    def is_audio_message(self, event):
        return self._assert_message_type(event, AudioMessage)

    @log_fsm_condition
    def is_location_message(self, event):
        return self._assert_message_type(event, LocationMessage)

    @log_fsm_condition
    def is_follow_event(self, event):
        return isinstance(event, FollowEvent)

    @log_fsm_condition
    def is_unfollow_event(self, event):
        return isinstance(event, UnfollowEvent)

    @log_fsm_condition
    def is_join_event(self, event):
        return isinstance(event, JoinEvent)

    @log_fsm_condition
    def is_leave_event(self, event):
        return isinstance(event, LeaveEvent)

    @log_fsm_condition
    def is_postback_event(self, event):
        return isinstance(event, PostbackEvent)

    @log_fsm_condition
    def is_beacon_event(self, event):
        return isinstance(event, BeaconEvent)


class DengueBotMachine(BotGraphMachine, LineBotEventConditionMixin):
    def __init__(self, states, transitions, initial_state='user', *,
                 bot_client, template_path, external_modules=None, root_path):
        self.config_path_base = root_path if root_path else ''
        self.load_config()
        super().__init__(
            states, transitions, initial_state,
            bot_client=bot_client, template_path=template_path, external_modules=None
        )

    def load_config(self):
        path = os.path.join(self.config_path_base, 'img_urls.json')
        with open(path) as img_url_file:
            self.img_urls = ujson.loads(img_url_file.read())

        self.LOCATION_SEND_TUTOIRAL_MSG = [
            ImageSendMessage(
                original_content_url=self.img_urls['loc_step1_origin'],
                preview_image_url=self.img_urls['loc_step1_preview']
            ),
            ImageSendMessage(
                original_content_url=self.img_urls['loc_step2_origin'],
                preview_image_url=self.img_urls['loc_step2_preview']
            ),
        ]

    def reply_message_with_logging(self, event, messages):
        receiver_id = event.source.user_id

        def save_message(msg):
            try:
                content = msg.text
            except AttributeError:
                content = '===This is {message_type} type message.==='.format(
                    message_type=msg.type
                )

            bot_reply_log = BotReplyLog(
                receiver=LineUser.objects.get(user_id=receiver_id),
                speak_time=datetime.now(),
                message_type=msg.type,
                content=content
            )
            bot_reply_log.save()

        self.bot_client.reply_message(event.reply_token, messages)

        if not isinstance(messages, (list, tuple)):
            messages = [messages]
        for m in messages:
            save_message(m)

    # -FSM conditions-
    @log_fsm_condition
    def is_pass(self, event):
        return True

    @log_fsm_condition
    def is_failed(self, event):
        return False

    # --None Text Condtions--
    @log_fsm_condition
    def is_selecting_ask_dengue_fever(self, event):
        return '1' == event.message.text or self.is_asking_dengue_fever(event)

    @log_fsm_condition
    def is_selecting_ask_symptom(self, event):
        return '2' == event.message.text or self.is_asking_symptom(event)

    @log_fsm_condition
    def is_selecting_ask_prevention(self, event):
        return '3' == event.message.text or self.is_asking_prevention(event)

    @log_fsm_condition
    def is_selecting_ask_hospital(self, event):
        return '4' == event.message.text or self.is_asking_hospital(event)

    @log_fsm_condition
    def is_selecting_ask_epidemic(self, event):
        return '5' == event.message.text or self.is_asking_epidemic(event)

    @log_fsm_condition
    def is_selecting_give_suggestion(self, event):
        return '6' == event.message.text or self.is_giving_suggestion(event)

    @log_fsm_condition
    def is_hospital_address(self, event):
        return 'hosptial_address' in parse_qs(event.postback.data)

    @log_fsm_condition
    def is_valid_address(self, event):
        coder = GoogleV3()
        address = event.message.text
        geocode = coder.geocode(address)
        return geocode is not None

    @log_fsm_operation
    def is_gov_report(self, event):
        return '#2016' in event.message.text

    # FSM Operations
    # --dynamic--
    def handle_custom_callback(self, callback):
        if callback.custom_type == 'text-finish':
            self.__dict__[callback.name] = partial(self._text_finish_base, template=callback.template)

    @log_fsm_operation
    def _text_finish_base(self, event, template):
        self._text_base(event, template)
        self.finish_ans()

    @log_fsm_operation
    def _text_base(self, event, template):
        self.reply_message_with_logging(
            event,
            TextSendMessage(text=super()._text_base(event, template))
        )

    # --helpers--
    _send_template_text = _text_base

    def _send_hospital_msgs(self, hospital_list, event):
        if hospital_list:
            msgs = self._create_hospitals_msgs(hospital_list)
        else:
            msgs = TextSendMessage(text=self.render_text('nearby_hospital/no_nearby_hospital.j2'))

        self.reply_message_with_logging(event, msgs)

    def _create_hospitals_msgs(self, hospital_list):
        carousel_messages = list()
        for hospital in hospital_list:
            name = hospital.get('name')
            address = hospital.get('address')
            phone = hospital.get('phone')

            carousel_messages.append(
                CarouselColumn(
                    text=name,
                    actions=[
                        PostbackTemplateAction(
                            label=address[:20],
                            text=' ',
                            data='hosptial_address='+address,
                        ),
                        MessageTemplateAction(
                            label=phone[:20],
                            text=' '
                        ),
                    ]
                )
            )

        carousel_messages.append(
            CarouselColumn(
                text=self.render_text('nearby_hospital/all_nearby.j2'),
                actions=[
                    MessageTemplateAction(
                        label=' ',
                        text=' '
                    ),
                    URITemplateAction(
                        label=self.render_text('nearby_hospital/label.j2'),
                        uri='https://www.taiwanstat.com/realtime/dengue-vis-with-hospital/',
                    )
                ]
            )
        )

        template_message = TemplateSendMessage(
            alt_text=self.render_text('nearby_hospital/alt_text.j2', {'hospitals': hospital_list}),
            template=CarouselTemplate(
                columns=carousel_messages
            )
        )

        hospital_messages = [template_message]
        return hospital_messages

    # --static--
    @log_fsm_operation
    def on_enter_user_join(self, event):
        # TODO: implement update user data when user rejoin
        user_id = event.source.user_id
        try:
            LineUser.objects.get(user_id=user_id)
        except LineUser.DoesNotExist:
            profile = self.bot_client.get_profile(user_id)
            user = LineUser(
                user_id=profile.user_id,
                name=profile.display_name,
                picture_url=profile.picture_url or '',
                status_message=profile.status_message or ''
            )
            user.save()
        self.finish()

    @log_fsm_operation
    def on_enter_unrecognized_msg(self, event):
        if getattr(event, 'reply_token', None):
            # TODO: Move datetime type casting to model
            msg_log = MessageLog.objects.get(speaker=event.source.user_id,
                                             speak_time=datetime.fromtimestamp(event.timestamp/1000),
                                             content=event.message.text)
            unrecognized_msg = UnrecognizedMsg(message_log=msg_log)
            unrecognized_msg.save()

            try:
                response_to_unrecog_msg = ResponseToUnrecogMsg.objects.get(
                    unrecognized_msg_content=unrecognized_msg.message_log.content
                )
            except ResponseToUnrecogMsg.DoesNotExist:
                self._send_template_text(event, 'unknown_msg.j2')
            else:
                response_content = response_to_unrecog_msg.content
                self.bot_client.reply_message(
                    event.reply_token,
                    TextSendMessage(text=response_content)
                )
        self.handle_unrecognized_msg(event)

    @log_fsm_operation
    def on_enter_ask_dengue_fever(self, event):
        KNOWLEDGE_URL = 'http://www.denguefever.tw/knowledge'
        QA_URL = 'http://www.denguefever.tw/qa'
        context = {
            'knowledge_url': KNOWLEDGE_URL,
            'qa_url': QA_URL
        }
        self.reply_message_with_logging(
            event,
            messages=TemplateSendMessage(
                alt_text=self.render_text('denguefever_intro/alt_text.j2', context),
                template=ButtonsTemplate(
                    text=self.render_text('denguefever_intro/intro_head.j2', {'is_button': True}),
                    actions=[
                        URITemplateAction(
                            label=self.render_text('denguefever_intro/intro_label.j2'),
                            uri=KNOWLEDGE_URL
                        ),
                        URITemplateAction(
                            label=self.render_text('denguefever_intro/qa_label.j2'),
                            uri=QA_URL
                        )
                    ]
                )
            )
        )
        self.finish_ans()

    @log_fsm_operation
    def on_enter_ask_symptom(self, event):
        self.reply_message_with_logging(
            event,
            messages=[
                ImageSendMessage(
                    original_content_url=self.img_urls['symptom_preview'],
                    preview_image_url=self.img_urls['symptom_origin']
                ),
                TextSendMessage(text=self.render_text('symptom_warning'))
            ]
        )
        self.finish_ans()

    @log_fsm_operation
    def on_enter_ask_prevention(self, event):
        text = self.render_text('ask_prevent_type.js')
        self.reply_message_with_logging(
            event,
            TemplateSendMessage(
                alt_text=text,
                template=ButtonsTemplate(
                    text=text,
                    actions=[
                        PostbackTemplateAction(
                            label=self.render_text('self_label.j2'),
                            data='自身'
                        ),
                        PostbackTemplateAction(
                            label=self.render_text('env_label.j2'),
                            data='環境'
                        ),
                    ]
                )
            )
        )

    @log_fsm_operation
    def on_enter_ask_hospital(self, event):
        messages = [
            TextSendMessage(text=self.render_text('ask_address.j2'))
        ]
        messages.extend(self.LOCATION_SEND_TUTOIRAL_MSG)
        self.reply_message_with_logging(
            event,
            messages=messages
        )
        self.advance()

    @log_fsm_operation
    def on_enter_receive_user_location(self, event):
        hospital_list = hospital.views.get_nearby_hospital(event.message.longitude,
                                                           event.message.latitude)
        self._send_hospital_msgs(hospital_list, event)
        self.finish_ans()

    @log_fsm_condition
    def on_enter_receive_user_address(self, event):
        coder = GoogleV3()
        address = event.message.text
        geocode = coder.geocode(address)
        hospital_list = hospital.views.get_nearby_hospital(geocode.longitude, geocode.latitude)
        self._send_hospital_msgs(hospital_list, event)
        self.finish_ans()

    @log_fsm_operation
    def on_enter_ask_hospital_map(self, event):
        address = parse_qs(event.postback.data)['hosptial_address'][0]
        hosp = hospital.models.Hospital.objects.using('tainan').get(address=address)
        self.bot_client.reply_message(
            event.reply_token,
            messages=LocationSendMessage(
                title=self.render_text('nearby_hospital/map_msg.j2', hosp.name),
                address=hosp.address,
                latitude=hosp.lat,
                longitude=hosp.lng
            )
        )
        self.finish_ans()

    @log_fsm_operation
    def on_enter_ask_epidemic(self, event):
        EPIDEMIC_LINK = 'http://www.denguefever.tw/realTime'
        context = {
            'link': EPIDEMIC_LINK
        }
        self.reply_message_with_logging(
            event,
            messages=TemplateSendMessage(
                alt_text=self.render_text('new_condition.j2', context),
                template=ButtonsTemplate(
                    text=self.render_text('new_condition.j2'),
                    actions=[
                        URITemplateAction(
                            label='Link',
                            uri=EPIDEMIC_LINK
                        )
                    ]
                )
            )
        )
        self.finish_ans()

    @log_fsm_operation
    def on_exit_wait_user_suggestion(self, event):
        self._send_template_text(event, 'thank_advice.j2')
        advice = Suggestion(content=event.message.text,
                            user=LineUser.objects.get(user_id=event.source.user_id))
        advice.save()

    @log_fsm_operation
    def on_enter_gov_faculty_report(self, event):
        text = event.message.text
        _, _, action, note = text.split('#')

        gov_report = GovReport(
            user=LineUser.objects.get(user_id=event.source.user_id),
            action=action,
            note=note,
            report_time=datetime.fromtimestamp(event.timestamp/1000),
        )
        gov_report.save()
        self.advance(event)

    @log_fsm_operation
    def on_enter_wait_gov_location(self, event):
        messages = [TextSendMessage(text=self.render_text('ask_gov_address.j2'))]
        messages.extend(self.LOCATION_SEND_TUTOIRAL_MSG)
        self.reply_message_with_logging(
            event,
            messages=messages
        )

    @log_fsm_operation
    def on_enter_receive_gov_location(self, event):
        try:
            gov_report = GovReport.objects.filter(
                user=LineUser.objects.get(user_id=event.source.user_id),
            ).order_by('-report_time')[0]
        except GovReport.DoesNotExist:
            logger.error('Gov Report Does Not Exist')
        else:
            gov_report.lat = event.message.latitude
            gov_report.lng = event.message.longitude
            gov_report.save()

            self.reply_message_with_logging(
                event,
                messages=TextSendMessage(text=self.render_text('thank_gov_report'))
            )
        self.finish_ans()


def generate_fsm_cls(cls_name, condition_config,
                     *, template_args=None, external_globals=None, cond_var_name=None):
    """Generate FSM class through condition config"""

    if not template_args:
        template_args = {
            'decorators': ['log_fsm_condition'],
            'func_args': ['self', 'event'],
            'preprocess_code': ['msg = event.message.text']
        }
    if not external_globals:
        external_globals = {
            'log_fsm_condition': log_fsm_condition
        }

    cond_funcs = cond_func_generator(
        condition_config,
        template_args=template_args,
        cond_var_name=cond_var_name or 'msg'
    )
    return CondMeta(cls_name, (DengueBotMachine,), dict(),
                    cond_funcs=cond_funcs, external_globals=external_globals)
