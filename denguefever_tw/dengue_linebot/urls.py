from django.conf.urls import url

from .views import *


urlpatterns = [
    url(r'^reply/$', reply),
    url(r'^$', index),
    url(r'^show_fsm/$', show_fsm, name='Show FSM'),
    url(r'^reload_fsm/$', reload_fsm, name='Reload FSM'),
    url(r'^user_list/$', user_list, name='User List'),
    url(r'^(?P<uid>\S+)/user_detail/$', user_detail, name='User Detail'),
    url(r'^msg_log_list/$', msg_log_list, name='Msg Log List'),
    url(r'^(?P<uid>\S+)/msg_log_detail/$', msg_log_detail,
        name='Msg Log Detail'),
    url(r'^unrecog_msgs/$', unrecognized_msg_list,
        name='Unrecognized Msg List'),
    url(r'^(?P<mid>\S+)/handle_unrecognized_msg/$', handle_unrecognized_msg,
        name='Handle Unrecognized Msg'),
    url(r'^suggestion_list/$', suggestion_list, name='Suggestion List'),
    url(r'^gov_report_list/$', gov_report_list, name='Gov Report List'),
    url(r'^export_msg_log/$', export_msg_log, name='Export Msg Log'),
    url(r'^push_msg/$', push_msg_form, name='Push Message'),
    url(r'^push_msg_result/$', push_msg_result, name='push_msg_result'),
    url(r'^area_list/$', area_list, name='area_list')
]
