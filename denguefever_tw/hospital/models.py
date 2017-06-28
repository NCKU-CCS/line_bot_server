from django.contrib.gis.db import models
from django.contrib.gis.geos import Point


class Hospital(models.Model):
    hospital_id = models.TextField(primary_key=True)
    name = models.TextField()
    address = models.TextField()
    phone = models.TextField()
    opening_hours = models.TextField()
    lng = models.FloatField()
    lat = models.FloatField()
    location = models.PointField(geography=True, srid=4326, default='POINT(0.0 0.0)')

    class Meta:
        unique_together = ('name', 'address', 'location')

    def save(self, *args, **kwargs):
        self.location = Point(float(self.lng), float(self.lat))
        super().save(*args, **kwargs)

    def __repr__(self):
        return self.name
