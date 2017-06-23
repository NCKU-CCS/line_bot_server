from django.contrib.gis.geos import GEOSGeometry
from django.db.utils import IntegrityError
from django.core.management.base import BaseCommand

import json

from ...models import MinArea


class Command(BaseCommand):
    help = 'Import Tainan Minarea Data'

    def handle(self, *args, **options):
        with open('dengue_linebot/data/tainan_minarea.json') as file:
            data = json.load(file)
            for area in data['features']:
                try:
                    minarea = MinArea(
                        area_id=area['properties']['VILLAGEID'],
                        area_sn=area['properties']['VILLAGESN'],
                        area_name=area['properties']['VILLAGENAM'],
                        district_name=area['properties']['TOWNNAME'],
                        area=GEOSGeometry(json.dumps(area['geometry']))
                    )
                    minarea.save()
                except IntegrityError:
                    self.stderr.write('data have already been imported')
                    break

        self.stdout.write('Successfully imported')
