import logging
import os
from datetime import datetime
from functools import wraps
from urllib.parse import parse_qs

import ujson
from geopy.geocoders import GoogleV3
from jsmin import jsmin
from transitions.extensions import GraphMachine
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

from .models import (
    LineUser, Suggestion, GovReport,
    UnrecognizedMsg, MessageLog, BotReplyLog, ResponseToUnrecogMsg
)
import hospital


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


class DengueBotMachine:
    def __init__(self, line_bot_api, initial_state='user', *,
                 root_path=None, language='zh_tw'):
        self.config_path_base = root_path if root_path else ''
        self.language = language
        self.load_config()
        self.machine = GraphMachine(
            model=self,
            states=self.states,
            transitions=self.dengue_transitions,
            initial=initial_state,
            auto_transitions=False,
            show_conditions=True
        )

        self.line_bot_api = line_bot_api

    def load_config(self):
        self.load_fsm_config()
        self.load_img_urls()
        self.load_msg()

    def load_fsm_config(self, filename='FSM.json'):
        path = os.path.join(self.config_path_base, filename)
        with open(path) as FSM_file:
            data = ujson.loads(jsmin(FSM_file.read()))

            self.states = data['states']
            self.dengue_transitions = data['transitions']

    def load_img_urls(self, filename='img_urls.json'):
        path = os.path.join(self.config_path_base, filename)
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

    def load_msg(self, filename='dengue_msg.json'):
        path = os.path.join(self.config_path_base, self.language)
        path = os.path.join(path, filename)
        with open(path) as msg_file:
            msgs = ujson.loads(jsmin(msg_file.read()))

            self.reply_msgs = msgs['reply_msgs']

    def draw_graph(self, filename, prog='dot'):
        self.graph.draw(filename, prog=prog)

    def set_state(self, state):
        self.machine.set_state(state)

    def reset_state(self):
        self.set_state('user')

    def reply_message_with_logging(self, reply_token, receiver_id, messages):
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

        self.line_bot_api.reply_message(reply_token, messages)

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

    # --Event Type Assertion--
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
    def _send_text_in_rule(self, event, key):
        self.reply_message_with_logging(
            event.reply_token,
            event.source.user_id,
            TextSendMessage(text=self.reply_msgs[key])
        )

    def _send_hospital_msgs(self, hospital_list, event):
        if hospital_list:
            msgs = self._create_hospitals_msgs(hospital_list)
        else:
            msgs = TextSendMessage(text=self.reply_msgs['no_nearby_hospital'])

        self.reply_message_with_logging(
            event.reply_token,
            event.source.user_id,
            msgs
        )

    def _create_hospitals_msgs(self, hospital_list):
        text = self.reply_msgs['nearby_msg_head']
        carousel_messages = list()
        for index, hospital in enumerate(hospital_list, 1):
            name = hospital.get('name')
            address = hospital.get('address')
            phone = hospital.get('phone')

            text += "\n\n{index}.{name}\n{address}\n{phone}".format(
                index=index,
                name=name,
                address=address,
                phone=phone
            )

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
                text=self.reply_msgs['nearby_hospital_list_head'],
                actions=[
                    MessageTemplateAction(
                        label=' ',
                        text=' '
                    ),
                    URITemplateAction(
                        label=self.reply_msgs['nearby_hospital_label'],
                        uri='https://www.taiwanstat.com/realtime/dengue-vis-with-hospital/',
                    )
                ]
            )
        )

        template_message = TemplateSendMessage(
            alt_text=text,
            template=CarouselTemplate(
                columns=carousel_messages
            )
        )

        hospital_messages = [template_message]
        return hospital_messages

    @log_fsm_operation
    def on_enter_user_join(self, event):
        # TODO: implement update user data when user rejoin
        user_id = event.source.user_id
        try:
            LineUser.objects.get(user_id=user_id)
        except LineUser.DoesNotExist:
            profile = self.line_bot_api.get_profile(user_id)
            user = LineUser(
                user_id=profile.user_id,
                name=profile.display_name,
                picture_url=profile.picture_url or '',
                status_message=profile.status_message or ''
            )
            user.save()
        self.finish()

    @log_fsm_operation
    def on_enter_greet(self, event):
        self._send_text_in_rule(event, 'greeting')
        self.finish_ans()

    @log_fsm_operation
    def on_enter_ask_who_we_are(self, event):
        self._send_text_in_rule(event, 'who_we_are')
        self.finish_ans()

    @log_fsm_operation
    def on_enter_ask_usage(self, event):
        self._send_text_in_rule(event, 'manual')

    @log_fsm_operation
    def on_enter_ask_breeding_source(self, event):
        self._send_text_in_rule(event, 'breeding_source')
        self.finish_ans()

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
                self._send_text_in_rule(event, 'unknown_msg')
            else:
                response_content = response_to_unrecog_msg.content
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=response_content)
                )
        self.handle_unrecognized_msg(event)

    @log_fsm_operation
    def on_enter_ask_dengue_fever(self, event):
        KNOWLEDGE_URL = 'http://www.denguefever.tw/knowledge'
        QA_URL = 'http://www.denguefever.tw/qa'
        self.reply_message_with_logging(
            event.reply_token,
            event.source.user_id,
            messages=TemplateSendMessage(
                alt_text=self.reply_msgs['dengue_fever_intro'],
                template=ButtonsTemplate(
                    text=self.reply_msgs['dengue_fever_intro_button'],
                    actions=[
                        URITemplateAction(
                            label=self.reply_msgs['dengue_intro_label'],
                            uri=KNOWLEDGE_URL
                        ),
                        URITemplateAction(
                            label=self.reply_msgs['dengue_qa_label'],
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
            event.reply_token,
            event.source.user_id,
            messages=[
                ImageSendMessage(
                    original_content_url=self.img_urls['symptom_preview'],
                    preview_image_url=self.img_urls['symptom_origin']
                ),
                TextSendMessage(text=self.reply_msgs['symptom_warning'])
            ]
        )
        self.finish_ans()

    @log_fsm_operation
    def on_enter_ask_prevention(self, event):
        self.reply_message_with_logging(
            event.reply_token,
            event.source.user_id,
            TemplateSendMessage(
                alt_text=self.reply_msgs['ask_prevent_type'],
                template=ButtonsTemplate(
                    text=self.reply_msgs['ask_prevent_type'],
                    actions=[
                        PostbackTemplateAction(
                            label=self.reply_msgs['self_label'],
                            data='自身'
                        ),
                        PostbackTemplateAction(
                            label=self.reply_msgs['env_label'],
                            data='環境'
                        ),
                    ]
                )
            )
        )

    @log_fsm_operation
    def on_enter_ask_self_prevention(self, event):
        self._send_text_in_rule(event, 'self_prevent')
        self.finish_ans()

    @log_fsm_operation
    def on_enter_ask_env_prevention(self, event):
        self._send_text_in_rule(event, 'env_prevent')
        self.finish_ans()

    @log_fsm_operation
    def on_enter_ask_hospital(self, event):
        messages = [
            TextSendMessage(text=self.reply_msgs['ask_address'])
        ]
        messages.extend(self.LOCATION_SEND_TUTOIRAL_MSG)
        self.reply_message_with_logging(
            event.reply_token,
            event.source.user_id,
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
        self.line_bot_api.reply_message(
            event.reply_token,
            messages=LocationSendMessage(
                title=self.reply_msgs['map_msg_template'].format(name=hosp.name),
                address=hosp.address,
                latitude=hosp.lat,
                longitude=hosp.lng
            )
        )
        self.finish_ans()

    @log_fsm_operation
    def on_enter_ask_epidemic(self, event):
        EPIDEMIC_LINK = 'http://www.denguefever.tw/realTime'
        self.reply_message_with_logging(
            event.reply_token,
            event.source.user_id,
            messages=TemplateSendMessage(
                alt_text=self.reply_msgs['new_condition']+EPIDEMIC_LINK,
                template=ButtonsTemplate(
                    text=self.reply_msgs['new_condition'],
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
    def on_enter_wait_user_suggestion(self, event):
        self._send_text_in_rule(event, 'ask_advice')

    @log_fsm_operation
    def on_exit_wait_user_suggestion(self, event):
        self._send_text_in_rule(event, 'thank_advice')
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
        messages = [TextSendMessage(text=self.reply_msgs['ask_gov_address'])]
        messages.extend(self.LOCATION_SEND_TUTOIRAL_MSG)
        self.reply_message_with_logging(
            event.reply_token,
            event.source.user_id,
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
                event.reply_token,
                event.source.user_id,
                messages=TextSendMessage(text=self.reply_msgs['thank_gov_report'])
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
