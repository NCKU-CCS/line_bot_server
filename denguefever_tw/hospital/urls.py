from django.conf.urls import url
from .views import hospital_insert, hospital_nearby


urlpatterns = [
    url(r'^insert/', hospital_insert),
    url(r'^nearby/', hospital_nearby),
]
