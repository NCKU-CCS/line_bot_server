from django.conf.urls import url
from .views import *


urlpatterns = [
    url(r'^reply/', reply),
    url(r'^show_fsm/', show_fsm),
    url(r'user_list/', user_list),
]
