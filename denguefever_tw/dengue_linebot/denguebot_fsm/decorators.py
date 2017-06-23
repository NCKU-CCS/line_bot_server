import logging
from functools import wraps


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
