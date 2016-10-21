from django.db import models


class LineUser(models.Model):
    user_id = models.TextField(primary_key=True)
    name = models.TextField()
    picture_url = models.TextField(blank=True)
    status_message = models.TextField(blank=True)

    def __str__(self):
        return '{} ({})'.format(self.name, self.user_id)
