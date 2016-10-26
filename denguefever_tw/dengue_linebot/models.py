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


class UnrecognizedMsg(models.Model):
    message = models.TextField()
    user_id = models.TextField()

    def __str__(self):
        return '{user_id} ({message})'.format(
            user_id=self.user_id,
            message=self.message
        )
