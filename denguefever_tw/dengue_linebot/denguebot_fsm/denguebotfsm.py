import logging
from datetime import datetime
from functools import partial
from urllib.parse import parse_qs

from geopy.geocoders import GoogleV3
from condconf import CondMeta, cond_func_generator
from linebot.models import (
    TextSendMessage, ImageSendMessage, LocationSendMessage,
    TemplateSendMessage, ImagemapSendMessage, BaseSize, ImagemapArea, CarouselTemplate,
    CarouselColumn, MessageTemplateAction, URITemplateAction,
    ButtonsTemplate, PostbackTemplateAction, URIImagemapAction, MessageImagemapAction
)

import hospital
from ..models import (
    LineUser, Suggestion, GovReport,
    UnrecognizedMsg, MessageLog, BotReplyLog, ResponseToUnrecogMsg, ReportZapperMsg
)
from .botfsm import BotGraphMachine, LineBotEventConditionMixin
from .decorators import log_fsm_condition, log_fsm_operation
from .constants import (
    SYMPTOM_PREVIEW_URL, SYMPTOM_ORIGIN_URL, KNOWLEDGE_URL, QA_URL,
    LOC_STEP1_PREVIEW_URL, LOC_STEP1_ORIGIN_URL, LOC_STEP2_PREVIEW_URL, LOC_STEP2_ORIGIN_URL,
)


logger = logging.getLogger(__name__)


class DengueBotMachine(BotGraphMachine, LineBotEventConditionMixin):
    LOCATION_SEND_TUTOIRAL_MSG = [
        ImageSendMessage(
            original_content_url=LOC_STEP1_ORIGIN_URL,
            preview_image_url=LOC_STEP1_PREVIEW_URL
        ),
        ImageSendMessage(
            original_content_url=LOC_STEP2_ORIGIN_URL,
            preview_image_url=LOC_STEP2_PREVIEW_URL
        ),
    ]
    SUPPORTED_LANGUAGES = {
        '1': 'zh_tw',
    }

    def __init__(self, states, transitions, initial_state='user', *,
                 bot_client, template_path, external_modules=None):
        super().__init__(
            states, transitions, initial_state,
            bot_client=bot_client, template_path=template_path, external_modules=external_modules
        )

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
    def is_selecting_register_location(self, event):
        return '7' == event.message.text

    @log_fsm_condition
    def is_selecting_zapper_func(self, event):
        return '8' == event.message.text

    @log_fsm_condition
    def is_selecting_bind_zapper(self, event):
        return '我要綁定補蚊燈！' == event.message.text

    @log_fsm_condition
    def is_selecting_zapper_problem(self, event):
        return '我的補蚊燈需要專人協助' == event.message.text

    @log_fsm_condition
    def is_hospital_address(self, event):
        return 'hosptial_address' in parse_qs(event.postback.data)

    @log_fsm_operation
    def is_gov_report(self, event):
        return '#2016' in event.message.text

    @log_fsm_operation
    def is_valid_language(self, event):
        text = event.message.text
        return text in self.SUPPORTED_LANGUAGES or text.lower() in self.SUPPORTED_LANGUAGES.values()

    @log_fsm_operation
    def is_invalid_language(self, event):
        return not self.is_valid_language(event)

    # FSM Operations
    # --dynamic--
    def handle_custom_callback(self, callback):
        if callback.custom_type == 'text-finish':
            self.__dict__[callback.name] = partial(self._text_finish_base, template=callback.template)

    @log_fsm_operation
    def _text_finish_base(self, event, template):
        self._send_template_text(event, template)
        self.finish_ans()

    # --helpers--
    def _send_template_text(self, event, template):
        self.reply_message_with_logging(
            event,
            TextSendMessage(text=super()._text_base(event, template))
        )

    _text_base = log_fsm_operation(_send_template_text)

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

    def _create_zapper_imgmap(self, event):
        zapper_imgmap = ImagemapSendMessage(
            base_url='https://i.imgur.com/9piGQjS.jpg',
            alt_text='user zapper information',
            base_size=BaseSize(height=1040, width=1040),
            actions=[
                URIImagemapAction(
                    link_uri='',
                    area=ImagemapArea(
                        x=0, y=0, width=520, height=520
                    )
                ),
                MessageImagemapAction(
                    text='我想了解整個商圈的蚊蟲情況',
                    area=ImagemapArea(
                        x=520, y=0, width=520, height=520
                    )
                ),
                MessageImagemapAction(
                    text='我的補蚊燈需要專人協助',
                    area=ImagemapArea(
                        x=0, y=520, width=520, height=520
                    )
                ),
                MessageImagemapAction(
                    text='我要綁定補蚊燈！',
                    area=ImagemapArea(
                        x=520, y=520, width=520, height=520
                    )
                ),
            ]
        )

        line_user = LineUser.objects.get(user_id=event.source.user_id)
        if line_user.zapper_id:
            zapper_imgmap.actions[0].link_uri = 'https://example.com/' + line_user.zapper_id
        return zapper_imgmap

    # --static--
    @log_fsm_operation
    def on_enter_user_join(self, event):
        user_id = event.source.user_id
        profile = self.bot_client.get_profile(user_id)
        user, created = LineUser.objects.get_or_create(user_id=profile.user_id)
        user.name = profile.display_name
        user.picture_url = profile.picture_url or ''
        user.status_message = profile.status_message or ''
        user.save()

        self._send_template_text(event, 'ask_language.j2')

    @log_fsm_operation
    def on_enter_receive_user_language(self, event):
        # FIXME
        language_choice = event.message.text
        language = self.SUPPORTED_LANGUAGES.get(language_choice)
        if not language:
            language = language_choice

        user_id = event.source.user_id
        user, created = LineUser.objects.get_or_create(user_id=user_id)
        user.language = language
        user.save()

        self.reply_message_with_logging(
            event,
            TextSendMessage(text=self.render_text('set_language_success.j2', {'language': language}))
        )

        self.finish(event)

    @log_fsm_operation
    def on_enter_unrecognized_msg(self, event):
        if getattr(event, 'reply_token', None):
            msg_log = MessageLog.objects.get(
                speaker=event.source.user_id,
                speak_time=datetime.fromtimestamp(event.timestamp/1000),
                content=event.message.text
            )
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
        self.reply_message_with_logging(
            event,
            messages=TemplateSendMessage(
                alt_text=self.render_text(
                    'denguefever_intro/alt_text.j2',
                    {
                        'knowledge_url': KNOWLEDGE_URL,
                        'qa_url': QA_URL
                    }
                ),
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
                    original_content_url=SYMPTOM_ORIGIN_URL,
                    preview_image_url=SYMPTOM_PREVIEW_URL
                ),
                TextSendMessage(text=self.render_text('symptom_warning.j2'))
            ]
        )
        self.finish_ans()

    @log_fsm_operation
    def on_enter_ask_prevention(self, event):
        text = self.render_text('ask_prevent_type.j2')
        self.reply_message_with_logging(
            event,
            TemplateSendMessage(
                alt_text=text,
                template=ButtonsTemplate(
                    text=text,
                    actions=[
                        PostbackTemplateAction(
                            label=self.render_text('label/self_label.j2'),
                            data='自身'
                        ),
                        PostbackTemplateAction(
                            label=self.render_text('label/env_label.j2'),
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
        hospital_list = hospital.utils.get_nearby_hospital(event.message.longitude,
                                                           event.message.latitude)
        self._send_hospital_msgs(hospital_list, event)
        self.finish_ans()

    @log_fsm_condition
    def on_enter_receive_user_address(self, event):
        coder = GoogleV3()
        address = event.message.text
        geocode = coder.geocode(address)
        if geocode:
            hospital_list = hospital.utils.get_nearby_hospital(geocode.longitude, geocode.latitude)
            self._send_hospital_msgs(hospital_list, event)
            self.finish_ans()
        else:
            # Invalid address
            self._send_text_in_rule(event, 'invalid_address')
            self.finish_ans()

    @log_fsm_operation
    def on_enter_ask_hospital_map(self, event):
        address = parse_qs(event.postback.data)['hosptial_address'][0]
        hosp = hospital.models.Hospital.objects.using('tainan').get(address=address)
        self.bot_client.reply_message(
            event,
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
        self.reply_message_with_logging(
            event,
            messages=TemplateSendMessage(
                alt_text=self.render_text('new_condition.j2', {'link': EPIDEMIC_LINK}),
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
        messages = [TextSendMessage(text=self.render_text('_ask_address.j2'))]
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

    @log_fsm_operation
    def on_enter_user_register_location(self, event):
        messages = [
            TextSendMessage(text=self.render_text('register_location.j2'))
        ]
        messages.extend(self.LOCATION_SEND_TUTOIRAL_MSG)
        self.reply_message_with_logging(
            event,
            messages=messages
        )
        self.advance()

    @log_fsm_operation
    def on_enter_receive_register_location(self, event):
        try:
            line_user = LineUser.objects.get(user_id=event.source.user_id)
        except LineUser.DoesNotExist:
            pass
        else:
            line_user.lat = event.message.latitude
            line_user.lng = event.message.longitude
            line_user.save()
            self._send_template_text(event, 'register_location_success.j2')
        self.finish_ans()

    @log_fsm_operation
    def on_enter_zapper_function(self, event):
        messages = [
            TextSendMessage(text=self.render_text('zapper_function.j2')),
        ]
        messages.append(self._create_zapper_imgmap(event))
        self.reply_message_with_logging(
            event,
            messages=messages
        )
        self.finish_ans()

    @log_fsm_operation
    def on_enter_receive_zapper_id(self, event):
        try:
            line_user = LineUser.objects.get(user_id=event.source.user_id)
        except LineUser.DoesNotExist:
            pass
        else:
            line_user.zapper_id = event.message.text
            line_user.save()

            messages = [
                TextSendMessage(text=self.render_text('bind_zapper_success.j2'))
            ]
            messages.append(self._create_zapper_imgmap(event))
            self.reply_message_with_logging(
                event,
                messages=messages
            )
        self.finish_ans()

    @log_fsm_operation
    def on_enter_receive_zapper_problem(self, event):
        self._send_template_text(event, 'thank_zapper_report.j2')
        report = ReportZapperMsg(
            reporter=LineUser.objects.get(user_id=event.source.user_id),
            report_time=datetime.fromtimestamp(event.timestamp/1000),
            content=event.message.text
        )
        report.save()
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
