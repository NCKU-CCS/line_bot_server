import os

import ujson
from transitions.extensions import GraphMachine
from linebot.models import (
    MessageEvent, FollowEvent, UnfollowEvent, JoinEvent, LeaveEvent, PostbackEvent, BeaconEvent,
    TextMessage, StickerMessage, ImageMessage, VideoMessage, AudioMessage, LocationMessage,
    TextSendMessage, ImageSendMessage, LocationSendMessage
)

from .models import LineUser

CONFIG_BASE_PATH = 'dengue_linebot/dengue_bot_config/'

symptom_preview_img_url = 'https://i.imgur.com/oydmUva.jpg'
symptom_origin_img_url = 'https://i.imgur.com/fs6wzor.jpg'


class DengueBotMachine:
    states = list()
    dengue_transitions = list()
    reply_msgs = dict()

    def __init__(self, line_bot_api, initial_state='user'):
        self.machine = GraphMachine(
            model=self,
            states=DengueBotMachine.states,
            transitions=DengueBotMachine.dengue_transitions,
            initial=initial_state,
            auto_transitions=False,
            show_conditions=True
        )
        self.line_bot_api = line_bot_api

    def draw_graph(self, filename, prog='dot'):
        self.graph.draw(filename, prog=prog)

    @staticmethod
    def load_config(filename='FSM.json'):
        path = os.path.join(CONFIG_BASE_PATH, filename)
        with open(path) as FSM_file:
            data = ujson.load(FSM_file)

        DengueBotMachine.states = data['states']
        DengueBotMachine.dengue_transitions = data['transitions']
        DengueBotMachine._add_unrecognized_traistion(data['states_needed_handle_unrecog_msg'])
        DengueBotMachine.load_msg()

    @staticmethod
    def _add_unrecognized_traistion(states):
        UNRECONGNIZED_STATE = 'unrecongnized_msg'
        DengueBotMachine.states.append(UNRECONGNIZED_STATE)
        DengueBotMachine.dengue_transitions.extend([
            {'trigger': 'advance',
             'source': state,
             'dest': UNRECONGNIZED_STATE,
             'conditions': 'is_pass'}
            for state in states
        ])
        DengueBotMachine.dengue_transitions.append(
            {
                'trigger': "handle_unrecognized_msg",
                'source': UNRECONGNIZED_STATE,
                'dest': 'user',
            }
        )

    @staticmethod
    def load_msg(filename='dengue_msg.json'):
        path = os.path.join(CONFIG_BASE_PATH, filename)
        with open(path) as msg_file:
            msgs = ujson.load(msg_file)
            DengueBotMachine.reply_msgs = msgs['reply_msgs']

    def set_state(self, state):
        self.machine.set_state(state)

    def is_pass(self, event):
        return True

    def is_failed(self, event):
        return False

    def _is_this_message_event(self, event, event_type):
        return isinstance(event, MessageEvent) and isinstance(event.message, event_type)

    def is_text_message(self, event):
        return self._is_this_message_event(event, TextMessage)

    def is_sticker_message(self, event):
        return self._is_this_message_event(event, StickerMessage)

    def is_image_message(self, event):
        return self._is_this_message_event(event, ImageMessage)

    def is_video_message(self, event):
        return self._is_this_message_event(event, VideoMessage)

    def is_audio_message(self, event):
        return self._is_this_message_event(event, AudioMessage)

    def is_location_message(self, event):
        return self._is_this_message_event(event, LocationMessage)

    def is_follow_event(self, event):
        return isinstance(event, FollowEvent)

    def is_unfollow_event(self, event):
        return isinstance(event, UnfollowEvent)

    def is_join_event(self, event):
        return isinstance(event, JoinEvent)

    def is_leave_event(self, event):
        return isinstance(event, LeaveEvent)

    def is_postback_event(self, event):
        return isinstance(event, PostbackEvent)

    def is_beacon_event(self, event):
        return isinstance(event, BeaconEvent)

    def is_asking_prevention(self, event):
        msg = event.message.text
        if (
            msg.strip() == "如何防範" or
            (any(m in msg for m in ["怎樣", "怎麼", "如何"]) and ("防疫" in msg)) or
            any(m in msg for m in ["防範", "預防"])
        ):
            return True
        return False

    def is_asking_self_prevention(self, event):
        return '自身' in event.message.text

    def is_asking_env_prevention(self, event):
        return '環境' in event.message.text

    def is_asking_dengue_fever(self, event):
        msg = event.message.text
        if any(m in msg for m in ["什麼是登革熱", "登革熱是什麼"]) or msg.strip() == "登革熱":
            return True
        return False

    def is_asking_who_we_are(self, event):
        msg = event.message.text
        if msg.strip() in ["你是誰", "掌蚊人是誰", "誰是掌蚊人", "掌蚊人"]:
            return True
        return False

    def is_asking_breeding_source(self, event):
        msg = event.message.text
        if (
            all(m in msg for m in ["登革熱", "孳生源"]) or
            (all(m in msg for m in ["孳生源", "是"]) and any(m in msg for m in ["什麼", "啥"]))
        ):
            return True
        return False

    def is_greeting(self, event):
        msg = event.message.text
        if any(m in msg.strip().lower() for m in ["哈囉", "你好", "嗨", "安安", "hello", "hi"]):
            return True
        return False

    def is_asking_hospital(self, event):
        msg = event.message.text
        if (
            msg.strip() in ["快篩檢驗", "快篩"] or
            (any(m in msg for m in ["最近", "附近", "去哪", "去那", "哪裡", "那裡", "在哪", "在那"]) and
             any(m in msg for m in ["快篩", "篩檢",  "檢查", "檢驗", "診所", "醫院"])) or
            all(m in msg for m in ["快篩", "診所"])
        ):
            return True
        return False

    def is_wrong_location(self, event):
        # TODO: implement
        return False

    def is_asking_symptom(self, event):
        msg = event.message.text
        if (
            msg.strip() in ["症狀", "登革熱症狀"] or
            all(m in msg for m in ["登革熱", "症狀"]) or
            all(m in msg for m in ["症狀", "是"])
        ):
            return True
        return False

    def is_asking_realtime_epidemic(self, event):
        msg = event.message.text
        if (
            msg.strip() in ["即時疫情", "疫情"] or
            (any(m in msg for m in ["最近", "本週", "這週"]) and ("疫情" in msg)) or
            ("疫情資訊" in msg)
        ):
            return True
        return False

    def is_giving_suggestion(self, event):
        return '建議' in event.message.text

    def is_asking_usage(self, event):
        msg = event.message.text
        if (
            msg.strip() in ["聊什麼", "翻譯蒟蒻"] or
            any(m in msg for m in ["使用說明", "功能"]) or
            (any(m in msg for m in ["可以", "能", "會"]) and
             any(m in msg for m in ["做啥", "幹麻", "幹嘛", "幹啥", "什麼", "幹什麼", "做什麼"])) or
            all(m in msg for m in ["有", "功能"]) or
            ("怎麼" in msg and any(m in msg for m in ["使用", "用"]))
        ):
            return True
        return False

    def is_selecting_ask_dengue_fever(self, event):
        return '1' in event.message.text

    def is_selecting_ask_symptom(self, event):
        return '2' in event.message.text

    def is_selecting_ask_prevention(self, event):
        return '3' in event.message.text

    def is_selecting_ask_hospital(self, event):
        return '4' in event.message.text

    def is_selecting_ask_realtime_epidemic(self, event):
        return '5' in event.message.text

    def is_selecting_give_suggestion(self, event):
        return '6' in event.message.text

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

    def _send_text_in_rule(self, event, key):
        resp = self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=DengueBotMachine.reply_msgs[key]
            )
        )
        return resp

    def on_enter_ask_prevention(self, event):
        resp = self._send_text_in_rule(event, 'ask_prevent_type')
        return resp

    def on_enter_ask_self_prevention(self, event):
        resp = self._send_text_in_rule(event, 'self_prevent')
        self.finish_ans()
        return resp

    def on_enter_ask_env_prevention(self, event):
        resp = self._send_text_in_rule(event, 'env_prevent')
        self.finish_ans()
        return resp

    def on_enter_ask_dengue_fever(self, event):
        resp = self._send_text_in_rule(event, 'dengue_fever_intro')
        self.finish_ans()
        return resp

    def on_enter_ask_hospital(self, event):
        resp = self._send_text_in_rule(event, 'ask_address')
        self.advance()
        return resp

    def on_enter_receive_user_location(self, event):
        # TODO: replace text with hospital location
        resp = self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='醫院')
        )
        # TODO: Implment hospital db
        # hospital_list = hospital.views.get_nearby_hospital(event.longitude, event.latitude)
        # if hospital_list:
        #     sender = self._send_hospitals(event, hospital_lst)
        #     msgs = self._create_hospitals_msgs(hospital_list)
        # else:
        #     msgs = [TextSendMessage(text="抱歉，你附近都沒有快篩診所\n")]
        #
        # msgs.append(
        #     TextSendMessage(text=(
        #         "想要查看地區所有快篩點，請點下面連結\n"
        #         "(如果手機不能瀏覽，可用電腦查看，或將連結貼到 chrome 瀏覽器)\n\n"
        #         "https://www.taiwanstat.com/realtime/dengue-vis-with-hospital/"))
        # )
        # resp = self.line_bot_api.reply_message(
        #     event.reply_token,
        #     msgs
        # )
        self.finish_ans()
        return resp

    # def _create_hospitals_msgs(self, hospital_list):
    #     text = "您好,\n最近的三間快篩診所是:"
    #     location_messages = list()
    #     for index, hospital in enumerate(hospital_list, 1):
    #         text += "\n\n{index}.{name}\n{address}\n{phone}".format(
    #             index=index
    #             name=hospital.get('name'),
    #             address=hospital.get('address'),
    #             phone=hospital.get('phone')
    #         )
    #
    #         location_message = LocationSendMessage(
    #             title="地圖 - {name}".format(name=hospital.get('name')),
    #             latitude=hospital.get('lat'),
    #             longitude=hospital.get('lng')
    #         )
    #
    #     text_message = TextSendMessage(text=text)
    #
    #     hospital_messages = [text_message]
    #     hospital_messages.extend(location_messages)
    #     return hospital_messages

    def on_enter_ask_symptom(self, event):
        resp = self.line_bot_api.reply_message(
            event.reply_token,
            messages=[
                ImageSendMessage(
                    original_content_url=symptom_origin_img_url,
                    preview_image_url=symptom_preview_img_url
                ),
                TextSendMessage(text=DengueBotMachine.reply_msgs['symptom_warning'])
            ]
        )
        self.finish_ans()
        return resp

    def on_enter_ask_realtime_epidemic(self, event):
        resp = self._send_text_in_rule(event, 'new_condition')
        self.finish_ans()
        return resp

    def on_enter_greet(self, event):
        resp = self._send_text_in_rule(event, 'greeting')
        self.finish_ans()
        return resp

    def on_enter_ask_breeding_source(self, event):
        resp = self._send_text_in_rule(event, 'breeding_source')
        return resp

    def on_enter_ask_who_we_are(self, event):
        resp = self._send_text_in_rule(event, 'who_we_are')
        return resp

    def on_enter_wait_user_suggestion(self, event):
        resp = self._send_text_in_rule(event, 'ask_advice')
        return resp

    def on_exit_wait_user_suggestion(self, event):
        resp = self._send_text_in_rule(event, 'thank_advice')
        # TODO: save suggestion
        # advice = Advice(advice=event.text, user_mid=reply_channel)
        # advice.save()
        return resp

    def on_enter_ask_usage(self, event):
        resp = self._send_text_in_rule(event, 'manual')
        return resp

    def on_enter_unrecongnized_msg(self, event):
        if getattr(event, 'reply_token', None):
            resp = self._send_text_in_rule(event, 'unknown_msg')
        self.handle_unrecognized_msg()
        return resp

    def handle_unrecognized_msg(self, event):
        # TODO: implement
        # random msg
        # 記錄不能辨別的訊息
        # unrecognize_msg = UnRecognizeMsg(user_mid=reply_channel, msg=msg)
        # unrecognize_msg.save()
        #
        # random.seed(time.time())
        # random_reply = random.choice(random_reply_lst)
        # reply_msg = random_reply['msg']
        # cache.set(reply_channel, random_reply['state'], timeout=30)
        pass


DengueBotMachine.load_config()
