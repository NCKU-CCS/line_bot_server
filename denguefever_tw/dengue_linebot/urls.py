from django.conf.urls import url
from .views import *

urlpatterns = [
    url('^reply/', reply),
    url('^show_fsm/', show_fsm)
]
