import shutil
import time

import yaml

STAMP = time.strftime("%Y%m%d%H%M%S")
PATH = "/config/automations.yaml"

shutil.copy(PATH, f"{PATH}.bak.{STAMP}")

with open(PATH, encoding="utf-8") as f:
    autos = yaml.safe_load(f)

restored = {
    "id": "1786612486482",
    "alias": "Hue Dimmer Schlafzimmer",
    "description": "Steuerung DachAchims Schlafzimmer Lampen",
    "triggers": [
        {"topic": "zigbee2mqtt/DG Achims Schlafzimmer Lichtschalter", "trigger": "mqtt"},
    ],
    "actions": [
        {"choose": [
            {"conditions": [{"condition": "template",
                              "value_template": "{{ trigger.payload_json.action == 'on_press' }}"}],
             "sequence": [{"target": {"entity_id": [
                 "light.dachachimsschlafzimmerleuchte1",
                 "light.dachachimsschlafzimmerleuchte2",
                 "light.dachachimsschlafzimmerleuchte3",
             ]}, "action": "light.turn_on"}]},
            {"conditions": [{"condition": "template",
                              "value_template": "{{ trigger.payload_json.action == 'off_press' }}"}],
             "sequence": [{"target": {"entity_id": [
                 "light.dachachimsschlafzimmerleuchte1",
                 "light.dachachimsschlafzimmerleuchte2",
                 "light.dachachimsschlafzimmerleuchte3",
             ]}, "action": "light.turn_off"}]},
            {"conditions": [{"condition": "template",
                              "value_template": "{{ trigger.payload_json.action == 'up_press' }}"}],
             "sequence": [{"target": {"entity_id": [
                 "light.dachachimsschlafzimmerleuchte1",
                 "light.dachachimsschlafzimmerleuchte2",
                 "light.dachachimsschlafzimmerleuchte3",
             ]}, "data": {"brightness_step_pct": 20}, "action": "light.turn_on"}]},
            {"conditions": [{"condition": "template",
                              "value_template": "{{ trigger.payload_json.action == 'down_press' }}"}],
             "sequence": [{"target": {"entity_id": [
                 "light.dachachimsschlafzimmerleuchte1",
                 "light.dachachimsschlafzimmerleuchte2",
                 "light.dachachimsschlafzimmerleuchte3",
             ]}, "data": {"brightness_step_pct": -20}, "action": "light.turn_on"}]},
        ]},
    ],
    "mode": "restart",
}

autos.append(restored)

with open(PATH, "w", encoding="utf-8") as f:
    yaml.safe_dump(autos, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

print("count now:", len(autos))
print("RESTORE_DONE")
