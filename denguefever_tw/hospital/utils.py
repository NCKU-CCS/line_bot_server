from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.forms.models import model_to_dict

from .models import Hospital


def get_nearby_hospital(lng, lat, *, database='tainan', limit=3, distance=5, exclude_fields=None):
    if not exclude_fields:
        exclude_fields = ['hospital_id', 'location', 'objects']

    point = Point(to_float(lng), to_float(lat), srid=4326)
    hospital_set = (
        Hospital.objects.using(database)
                .annotate(distance=Distance('location', point))
                .filter(location__distance_lte=(point, D(km=5)))
                .order_by('distance')[:limit]
    )

    response_data = [model_to_dict(hospital, exclude=exclude_fields)
                     for hospital in hospital_set]
    return response_data


def to_float(f):
    try:
        return float(f)
    except ValueError:
        return -1
