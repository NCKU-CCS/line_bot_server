from django.conf.urls import url
from .views import *

urlpatterns = [
    url('^reply/', reply),
    url('^broadcast/', broadcast),
]
