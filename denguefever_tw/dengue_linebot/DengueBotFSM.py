import os

import ujson
from transitions.extensions import GraphMachine
# import requests


CONFIG_BASE_PATH = 'dengue_linebot/dengue_bot_config/'

INITIAL_STATE = 'user'
UNRECONGNIZED_STATE = 'unrecongnized_msg'
TRANSITION_TO_UNRECONGNIZED = 'receive_unrecognized_msg'

symptom_preview_img_url = 'https://i.imgur.com/oydmUva.jpg'
symptom_origin_img_url = 'https://i.imgur.com/fs6wzor.jpg'


class DengueBotMachine:
    states = list()
    dengue_transitions = list()
    reply_msgs = dict()

    def __init__(self, initial_state='user'):
        self.machine = GraphMachine(
            model=self,
            states=DengueBotMachine.states,
            transitions=DengueBotMachine.dengue_transitions,
            initial=initial_state,
            auto_transitions=False,
            show_conditions=True
        )

    def draw_graph(self, filename, prog='dot'):
        self.graph.draw(filename, prog=prog)

    @staticmethod
    def load_config(filename='FSM.json'):
        path = os.path.join(CONFIG_BASE_PATH, filename)
        with open(path) as FSM_file:
            data = ujson.load(FSM_file)

        DengueBotMachine.states = data['states']
        DengueBotMachine.dengue_transitions = data['transitions']
        DengueBotMachine._add_unrecognized_traistion()
        DengueBotMachine.load_msg()

    @staticmethod
    def _add_unrecognized_traistion():
        other_states = list(set(DengueBotMachine.states) - set([INITIAL_STATE]))
        DengueBotMachine.states.append(UNRECONGNIZED_STATE)
        back_transitions = [
            {'trigger': TRANSITION_TO_UNRECONGNIZED,
             'source': state,
             'dest': UNRECONGNIZED_STATE}
            for state in other_states
        ]
        DengueBotMachine.dengue_transitions.extend(back_transitions)
        DengueBotMachine.dengue_transitions.extend([
            {
                'trigger': "handle_unrecognized_msg",
                'source': UNRECONGNIZED_STATE,
                'dest': 'user'
            }
        ])

    @staticmethod
    def load_msg(filename='dengue_msg.json'):
        path = os.path.join(CONFIG_BASE_PATH, filename)
        with open(path) as msg_file:
            msgs = ujson.load(msg_file)
            DengueBotMachine.reply_msgs = msgs['reply_msgs']

    def is_pass(self, handler):
        return True

    def is_failed(self, handler):
        return False

    def is_asking_dengue_fever(self, handler):
        msg = handler.text
        if msg.strip() == "登革熱" or "什麼是登革熱" in msg or "登革熱是什麼" in msg:
            return True
        return False

    def is_asking_who_we_are(self, handler):
        msg = handler.text
        if msg.strip() in ["你是誰", "掌蚊人是誰", "誰是掌蚊人", "掌蚊人"]:
            return True
        return False

    def is_asking_breeding_source(self, handler):
        msg = handler.text
        if (
            ("登革熱" in msg and "孳生源" in msg) or
            ("孳生源" in msg and "是" in msg and ("什麼" in msg or "啥" in msg))
        ):
            return True
        return False

    def is_greeting(self, handler):
        msg = handler.text
        if (
            msg.strip().lower() == "hello" or msg.strip().lower() == "hi" or
            "哈囉" in msg or "你好" in msg or "嗨" in msg or "安安" in msg or
            "hello" in msg or "hi" in msg or "HI" in msg
        ):
            return True
        return False

    def is_asking_prevetion(self, handler):
        msg = handler.text
        if (
            msg.strip() == "如何防範" or
            (("怎樣" in msg or "怎麼" in msg or "如何" in msg) and ("防疫" in msg)) or
            "防範" in msg or "預防" in msg
        ):
            return True
        return False

    def is_asking_self_prevetion(self, handler):
        return '自身' in handler.text

    def is_asking_env_prevetion(self, handler):
        return '環境' in handler.text

    def is_asking_hospital(self, handler):
        msg = handler.text
        if (
            msg.strip() == "快篩" or msg.strip() == "快篩檢驗" or
            (("最近" in msg or "附近" in msg or "去哪" in msg or "去那" in msg or "哪裡" in msg or "那裡" in msg or "在哪" in msg or "在那" in msg) and
             ("快篩" in msg or "篩檢" in msg or "檢查" in msg or "檢驗" in msg or "診所" in msg or "醫院" in msg)) or
            (("快篩" in msg) and ("診所" in msg))
        ):
            return True
        return False

    def is_wrong_location(self, handler):
        pass

    def is_user_cur_location(self, handler):
        return bool(handler.location)

    def is_asking_symptom(self, handler):
        msg = handler.text
        if (
            msg.strip() == "症狀" or
            msg.strip() == "登革熱症狀" or
            ("登革熱" in msg and "症狀" in msg) or
            ("症狀" in msg and "是" in msg)
        ):
            return True
        return False

    def is_asking_realtime_epidemic(self, handler):
        msg = handler.text
        if (
            msg.strip() == "即時疫情" or msg.strip() == "疫情" or
            (("最近" in msg or "本週" in msg or "這週" in msg) and ("疫情" in msg)) or
            ("疫情資訊" in msg)
        ):
            return True
        return False

    def is_giving_suggestion(self, handler):
        return '建議' in handler.text

    def is_asking_usage(self, handler):
        msg = handler.text
        if (
            msg.strip() == "聊什麼" or msg.strip() == "翻譯蒟蒻" or
            "使用說明" in msg or "功能" in msg or
            (("可以" in msg or "能" in msg or "會" in msg) and
             ("做啥" in msg or "幹麻" in msg or "幹嘛" in msg or "幹啥" in msg or
             "什麼" in msg or "幹什麼" in msg or "做什麼" in msg)) or
            ("有" in msg and "功能" in msg) or
            ("怎麼" in msg and ("用" in msg or "使用" in msg))
        ):
            return True
        return False

    def is_selecting_ask_dengue_fever(self, handler):
        return '1' in handler.text

    def is_selecting_ask_symptom(self, handler):
        return '2' in handler.text

    def is_selecting_ask_prevention(self, handler):
        return '3' in handler.text

    def is_selecting_ask_hopital(self, handler):
        return '4' in handler.text

    def is_selecting_ask_realtime_epidemic(self, handler):
        return '5' in handler.text

    def is_selecting_give_suggestion(self, handler):
        return '6' in handler.text

    def on_enter_ask_prevention(self, handler):
        resp = self._send_text_in_rule(handler, 'ask_prevent_type')
        return resp

    def on_enter_ask_self_prevention(self, handler):
        resp = self._send_text_in_rule(handler, 'self_prevent')
        self.finish_ans()
        return resp

    def on_enter_ask_env_prevention(self, handler):
        resp = self._send_text_in_rule(handler, 'env_prevent')
        self.finish_ans()
        return resp

    def on_enter_ask_usage(self, handler):
        resp = self._send_text_in_rule(handler, 'manual')
        return resp

    def on_enter_ask_hospital(self, handler):
        resp = self._send_text_in_rule(handler, 'ask_address')
        return resp

    def on_enter_receive_user_location(self, handler):
        # TODO: implement hospital part
        resp = handler._client.send_text(
            to_mid=handler.user_mid,
            text='醫院'
        )
        return resp

    # def receive_address(self, handler):
    #     # TODO: hospital db
    #     hospital_list = hospital.views.get_nearby_hospital(handler.longitude, handler.latitude)
    #     if hospital_list:
    #         sender = send_hospitals(handler, hospital_lst)
    #     else:
    #         resq = requests.Request()
    #         resq.status_code = 404
    #         return resq
    #
    #     sender.add_text(text=("想要查看地區所有快篩點，請點下面連結\n"
    #                           "(如果手機不能瀏覽，可用電腦查看，或將連結貼到 chrome 瀏覽器)\n\n"
    #                           "https://www.taiwanstat.com/realtime/dengue-vis-with-hospital/"))
    #     return sender.send(to_mid=handler.user_mid)
    #
    # def _send_hospitals(self, handler):
    #     mul_msg_sender = handler.client.multiple_message
    #
    #     text = "您好,\n最近的三間快篩診所是:"
    #     for index, hospital in enumerate(hospital_list, 1):
    #         text += "\n\n{index}.{name}\n{address}\n{phone}".format(
    #             index=index
    #             name=hospital.get('name'),
    #             address=hospital.get('address'),
    #             phone=hospital.get('phone')
    #         )
    #     mul_msg_sender.add_text(text=text)
    #
    #     for hospital in hospital_list:
    #         mul_msg_sender.add_location(title="地圖 - {name}".format(name=hospital.get('name')),
    #                                     latitude=hospital.get('lat'),
    #                                     longitude=hospital.get('lng'))
    #     return mul_msg_sender
    #

    def on_enter_ask_dengue_fever(self, handler):
        resp = self._send_text_in_rule(handler, 'dengue_fever_intro')
        self.finish_ans()
        return resp

    def on_enter_ask_realtime_epidemic(self, handler):
        resp = self._send_text_in_rule(handler, 'new_condition')
        self.finish_ans()
        return resp

    def on_enter_ask_symptom(self, handler):
        resp = (handler._client.multiple_message
                .add_image(image_url=symptom_origin_img_url,
                           preview_url=symptom_preview_img_url)
                .add_text(DengueBotMachine.reply_msgs['symptom_warning'])
                .send())
        self.finish_ans()
        return resp

    def on_enter_wait_user_suggestion(self, handler):
        resp = self._send_text_in_rule(handler, 'ask_advice')
        return resp

    def on_enter_greeting(self, handler):
        resp = self._send_text_in_rule(handler, 'greeting')
        return resp

    def on_enter_ask_breeding_source(self, handler):
        resp = self._send_text_in_rule(handler, 'breeding_source')
        return resp

    def ask_who_we_are(self, handler):
        resp = self._send_text_in_rule(handler, 'who_we_are')
        return resp

    def on_exit_wait_user_suggestion(self, handler):
        resp = self._send_text_in_rule(handler, 'thank_advice')
        # TODO: save suggestion
        # advice = Advice(advice=handler.text, user_mid=reply_channel)
        # advice.save()
        return resp

    def on_enter_unrecongnized_msg(self, handler):
        resp = self._send_text_in_rule(handler, 'unknown_msg')
        # random msg
        # 記錄不能辨別的訊息
        # unrecognize_msg = UnRecognizeMsg(user_mid=reply_channel, msg=msg)
        # unrecognize_msg.save()
        #
        # random.seed(time.time())
        # random_reply = random.choice(random_reply_lst)
        # reply_msg = random_reply['msg']
        # cache.set(reply_channel, random_reply['state'], timeout=30)
        self.handle_unrecognized_msg()
        return resp

    def _send_text_in_rule(self, handler, key):
        resp = handler._client.send_text(
            to_mid=handler.user_mid,
            text=DengueBotMachine.reply_msgs[key]
        )
        return resp

    def handle_unrecognized_msg(self):
        # TODO: implement
        pass

DengueBotMachine.load_config()
