import sys
import time
import requests

file_path = sys.argv[1]
with open(file_path, 'r') as myfile:
    data = myfile.read()

for line in data.split('\n'):
    line_split = line.split('\t')
    name = line_split[0]
    address = line_split[1]

    if len(line_split) >= 3:
        phone = line_split[2]
    else:
        phone = ""
    
    lat = line_split[3]
    lng = line_split[4]

    payload = {"database": "tainan", "name": name, "address": address, "phone": phone, "opening_hours": "", "lng": lng, "lat": lat}
    print (payload)
    req = requests.post('http://localhost:8000/hospital/insert/', data=payload)
    print (req)

    time.sleep(1.5)
