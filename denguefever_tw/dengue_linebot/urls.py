from django.conf.urls import url

from .views import *


urlpatterns = [
    url(r'^reply/$', reply),
    url(r'^$', index),
    url(r'^show_fsm/$', show_fsm),
    url(r'^reload_fsm/$', reload_fsm),
    url(r'^user_list/$', user_list),
    url(r'^(?P<uid>\S+)/user_detail/$', user_detail),
    url(r'^msg_log_list/$', msg_log_list),
    url(r'^(?P<uid>\S+)/msg_log_detail/$', msg_log_detail),
    url(r'^unrecog_msgs/$', unrecognized_msg_list),
    url(r'^(?P<mid>\S+)/handle_unrecognized_msg/$', handle_unrecognized_msg),
    url(r'^suggestion_list/$', suggestion_list),
    url(r'^gov_report_list/$', gov_report_list),
    url(r'^export_msg_log/$', export_msg_log),
    url(r'^push_msg/$', push_msg_form),
    url(r'^push_msg_result/$', push_msg_result, name='push_msg_result'),
]
