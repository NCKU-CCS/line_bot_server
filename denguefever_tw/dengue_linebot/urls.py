from django.conf.urls import url
from .views import *


urlpatterns = [
    url(r'^reply/', reply),
    url(r'^show_fsm/', show_fsm),
    url(r'user_list/', user_list),
    url(r'msg_log_list/', msg_log_list),
    url(r'^(?P<uid>\S+)/msg_log_detail/', msg_log_detail),
]
