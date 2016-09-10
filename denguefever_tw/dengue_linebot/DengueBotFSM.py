import os

import ujson
from transitions.extensions import GraphMachine


CONFIG_BASE_PATH = 'dengue_linebot/dengue_bot_config/'

INITIAL_STATE = 'user'
UNRECONGNIZED_STATE = 'unrecongnized_msg'
TRANSITION_TO_UNRECONGNIZED = 'receive_unrecognized_msg'


class DengueBotMachine:
    states = list()
    dengue_transitions = list()

    def __init__(self, initial_state='user'):
        self.machine = GraphMachine(
            model=self,
            states=DengueBotMachine.states,
            transitions=DengueBotMachine.dengue_transitions,
            initial=initial_state,
            auto_transitions=False,
            show_conditions=True
        )

    @property
    def graph(self):
        return self.machine.graph

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


DengueBotMachine.load_config()
