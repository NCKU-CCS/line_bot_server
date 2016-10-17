import json
import shortuuid

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from hospital.models import Hospital


@csrf_exempt
def hospital_insert(request):
    if request.method != 'POST':
        return HttpResponse(status=405)

    database = request.POST.get('database', '')
    hospital_id = shortuuid.uuid()
    name = request.POST.get('name', '')
    address = request.POST.get('address', '')
    phone = request.POST.get('phone', '')
    opening_hours = request.POST.get('opening_hours', '')
    lng = request.POST.get('lng', '')
    lat = request.POST.get('lat', '')

    hospital = Hospital(
            hospital_id=hospital_id,
            name=name,
            address=address,
            phone=phone,
            opening_hours=opening_hours,
            lng=lng,
            lat=lat)
    hospital.save(using=database)
    return HttpResponse(status=200)

def get_nearby_hospital(lng, lat, database='tainan'):
    point = Point(_toFloat(lng), _toFloat(lat), srid=4326)
    hospital_set = Hospital.objects.using(database)\
            .annotate(distance=Distance('location', point))\
            .filter(location__distance_lte=(point, D(km=5)))\
            .order_by('distance')
    
    
    hospital_set = hospital_set[:3]
    response_data = []
    for hospital in hospital_set:
        response_data_tmp = model_to_dict(hospital, exclude=['hospital_id', 'location', 'objects'])
        response_data.append(response_data_tmp)
    return response_data


def hospital_nearby(request):
#    if request.method != 'GET' or request.user.is_authenticated() == False:
#        return HttpResponse(status=405)

    database = request.GET.get('database', '')
    lng = request.GET.get('lng', '')
    lat = request.GET.get('lat', '')

    if database == '' or lng == '' or lat == '':
        return HttpResponse(status=406)

    point = Point(_toFloat(lng), _toFloat(lat), srid=4326)
    hospital_set = Hospital.objects.using(database)\
            .annotate(distance=Distance('location', point))\
            .filter(location__distance_lte=(point, D(km=5)))\
            .order_by('distance')
    
    # hospital_set = hospital_set[:3]
    response_data = []
    for hospital in hospital_set:
        response_data_tmp = model_to_dict(hospital, exclude=['hospital_id', 'location', 'objects'])
        response_data_tmp['distance'] = str(hospital.distance)
        response_data.append(response_data_tmp)
    return HttpResponse(json.dumps(response_data), status=200, content_type='application/json')


def _toFloat(f):
    try:
        return float(f)
    except:
        return -1
