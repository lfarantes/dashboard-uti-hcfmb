#!/usr/bin/env python
import requests
data = {
    'token': '214FFE1567BA30B88DF4ED0A80D648F6',
    'content': 'project',
    'format': 'json',
    'returnFormat': 'json'
}
r = requests.post('https://redcap.hcfmb.unesp.br/api/',data=data)
print('HTTP Status: ' + str(r.status_code))
print(r.json())
