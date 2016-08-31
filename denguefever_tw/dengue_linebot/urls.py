from django.conf.urls import url
from .views import reply

urlpatterns = [
    url('^reply/', reply),
]
