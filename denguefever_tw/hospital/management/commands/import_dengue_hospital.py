from django.db.utils import IntegrityError
from django.core.management.base import BaseCommand

import csv
import shortuuid
import logging

from ...models import Hospital

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import Hospital Data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            default='hospital/data/tainan_hospitals.tsv'
        )
        parser.add_argument(
            '--database',
            default='tainan'
        )

    def handle(self, *args, **options):
        with open(options['path'], 'r') as input_data:
            data = csv.reader(input_data, delimiter='\t')
            for row in data:
                name, address, phone, lat, lng = row
                logger.info(row)

                try:

                    hospital = Hospital(
                        hospital_id=shortuuid.uuid(),
                        name=name,
                        address=address,
                        phone=phone,
                        opening_hours='',
                        lng=lng,
                        lat=lat
                    )
                    hospital.save(using=options['database'])
                except IntegrityError:
                    print('data have already been imported')
                    break
