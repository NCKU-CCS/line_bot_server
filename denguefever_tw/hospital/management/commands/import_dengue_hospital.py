from django.core.management.base import BaseCommand

import time
import csv

import requests


class Command(BaseCommand):
    help = 'Import Hospital Data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            default='hospital/data/tainan_hospitals.tsv'
        )

    def handle(self, *args, **options):
        with open(options['path'], 'r') as input_data:
            data = csv.reader(input_data, delimiter='\t')
            for row in data:
                name, address, phone, lat, lng = row

                payload = {"database": "tainan", "name": name, "address": address, "phone": phone, "opening_hours": "", "lng": lng, "lat": lat}
                print(payload)
                req = requests.post('http://localhost:8000/hospital/insert/', data=payload)
                print(req)

                time.sleep(1.5)
