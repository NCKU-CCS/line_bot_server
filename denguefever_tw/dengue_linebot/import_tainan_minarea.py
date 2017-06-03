from django.contrib.gis.geos import GEOSGeometry
from .models import MinArea
import json

def f():
    with open('dengue_linebot/data/tainan_minarea.json') as file:
        data = json.load(file)
        for area in data['features']:
            try:
                print('importing...'+area['properties']['VILLAGEID'])
                minarea = MinArea(
                    area_id=area['properties']['VILLAGEID'],
                    area_sn=area['properties']['VILLAGESN'],
                    area=GEOSGeometry(json.dumps(area['geometry']))
                )
                minarea.save()
            except:
                break



