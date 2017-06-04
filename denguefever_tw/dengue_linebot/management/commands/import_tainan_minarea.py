from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand, CommandError

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
                        area=GEOSGeometry(json.dumps(area['geometry']))
                    )
                    minarea.save()
                except IntegrityError:
                    print('data have already been imported')
                    break

        self.stdout.write('Successfully imported')