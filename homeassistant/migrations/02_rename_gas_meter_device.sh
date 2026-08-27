#!/bin/sh
set -e
python3 -c "
import json

path = '/config/.storage/core.device_registry'
with open(path, encoding='utf-8') as f:
    data = json.load(f)

target_id = '58508c30b174a92971c1b4477f4a9827'
found = False
for d in data['data']['devices']:
    if d.get('id') == target_id:
        d['name_by_user'] = 'Keller Gasreader'
        found = True
        break

if not found:
    raise SystemExit('device not found')

with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
print('RENAME_APPLIED')
"
