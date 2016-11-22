from django.db import models


class LineUser(models.Model):
    user_id = models.TextField(primary_key=True)
    name = models.TextField()
    picture_url = models.TextField(blank=True)
    status_message = models.TextField(blank=True)

    def __str__(self):
        return '{name} ({user_id})'.format(
            name=self.name,
            user_id=self.user_id
        )


class Advice(models.Model):
    content = models.TextField()
    user_id = models.TextField()

    def __str__(self):
        return '{user_id}: {content}'.format(
            user_id=self.user_id,
            content=self.content
        )


class MessageLog(models.Model):
    speaker = models.ForeignKey(LineUser, related_name='message_log')
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
    receiver = models.ForeignKey(LineUser, related_name='bot_reply_log')
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

    def __str__(self):
        return self.__repr__()


class UnrecognizedMsg(models.Model):
    message_log = models.ForeignKey(MessageLog,
                                    related_name='unrecognized_message_log')

    def __str__(self):
        return str(self.message_log)
