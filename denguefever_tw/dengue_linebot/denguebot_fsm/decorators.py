import logging
from functools import wraps


logger = logging.getLogger(__name__)


def log_fsm_condition(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        logger.info('%s is %s\n', func.__name__, result)
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
             'Beforce Advance: %s\n'
             'Triggered Function: %s\n'
             'After Advance: %s\n'),
            pre_state, func.__name__, post_state
        )
        return result
    return wrapper
