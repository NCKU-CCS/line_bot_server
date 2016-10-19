import os

import ujson
from transitions.extensions import GraphMachine
from linebot.models import (
    MessageEvent, FollowEvent, UnfollowEvent, JoinEvent, LeaveEvent, PostbackEvent, BeaconEvent,
    TextMessage, StickerMessage, ImageMessage, VideoMessage, AudioMessage, LocationMessage,
    TextSendMessage
)

from .models import LineUser

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


DengueBotMachine.load_config()
