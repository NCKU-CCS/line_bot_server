from django.contrib.gis.db import models
from django.contrib.gis.geos import Point

import logging


logger = logging.getLogger(__name__)


class LineUser(models.Model):
    user_id = models.TextField(primary_key=True)
    name = models.TextField()
    picture_url = models.TextField(blank=True)
    status_message = models.TextField(blank=True)
    language = models.TextField(default='zh_tw')
    lng = models.FloatField(default=0.0)
    lat = models.FloatField(default=0.0)
    location = models.ForeignKey('MinArea', null=True, on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
        if self.lng and self.lat:
            try:
                self.location = MinArea.objects.get(area__contains=Point(float(self.lng), float(self.lat)))
            except MinArea.DoesNotExist:
                logger.error('The location of the user can not match any minarea')
        super(LineUser, self).save(*args, **kwargs)

    def __str__(self):
        return '{name} ({user_id})'.format(
            name=self.name,
            user_id=self.user_id
        )


class MinArea(models.Model):
    area_id = models.TextField()
    area_sn = models.TextField(primary_key=True)
    area_name = models.TextField(null=True)
    district_name = models.TextField(null=True)
    area = models.PolygonField(srid=4326)

    def __str__(self):
        return ' {district} {area}'.format(
            district=self.district_name,
            area=self.area_name
        )


class Suggestion(models.Model):
    content = models.TextField()
    user = models.ForeignKey(LineUser, related_name='suggestion', on_delete=models.CASCADE)

    def __str__(self):
        return '{user}: {content}'.format(
            user=self.user.name,
            content=self.content
        )


class MessageLog(models.Model):
    speaker = models.ForeignKey(LineUser, related_name='message_log', on_delete=models.CASCADE)
    speak_time = models.DateTimeField()
    message_type = models.TextField()
    content = models.TextField(null=True, blank=True)

    def __str__(self):
        speaker = self.speaker
        try:
            user = LineUser.objects.get(user_id=self.speaker)
            speaker = user.name
        except LineUser.DoesNotExist:
            pass
        return '{speak_time}\n{message_type}\n {speaker}: {content}'.format(
            speaker=speaker,
            message_type=self.message_type,
            speak_time=self.speak_time,
            content=self.content
        )


class BotReplyLog(models.Model):
    receiver = models.ForeignKey(LineUser, related_name='bot_reply_log', on_delete=models.CASCADE)
    speak_time = models.DateTimeField()
    message_type = models.TextField()
    content = models.TextField(null=True, blank=True)

    def __repr__(self):
        return '{speak_time}\n{message_type}\n BOT (to {receiver}): {content}'.format(
            receiver=self.receiver,
            message_type=self.message_type,
            speak_time=self.speak_time,
            content=self.content
        )


class UnrecognizedMsg(models.Model):
    message_log = models.ForeignKey(MessageLog, related_name='unrecognized_message_log', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.message_log)


class ResponseToUnrecogMsg(models.Model):
    unrecognized_msg_content = models.TextField(unique=True)
    content = models.TextField()

    def __str__(self):
        return 'Unrecognized Message: {unrecog_msg}\nResponse: {proper_response}'.format(
            unrecog_msg=self.unrecognized_msg_content,
            proper_response=self.content
        )


class GovReport(models.Model):
    user = models.ForeignKey(LineUser, related_name='gov_faculty', on_delete=models.CASCADE)
    action = models.TextField()
    note = models.TextField()
    report_time = models.DateTimeField()
    lng = models.FloatField(default=0.0)
    lat = models.FloatField(default=0.0)
    location = models.PointField(geography=True, srid=4326, default='POINT(0.0 0.0)')

    def save(self, **kwargs):
        if self.lng and self.lat:
            self.location = Point(float(self.lng), float(self.lat))
        super(GovReport, self).save(**kwargs)
