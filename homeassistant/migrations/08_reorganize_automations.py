import shutil
import time

import yaml

STAMP = time.strftime("%Y%m%d%H%M%S")
PATH = "/config/automations.yaml"

shutil.copy(PATH, f"{PATH}.bak.{STAMP}")

with open(PATH, encoding="utf-8") as f:
    autos = yaml.safe_load(f)

by_id = {a["id"]: a for a in autos}

# --- 1. Simple renames ---
by_id["1728192892663"]["alias"] = "DG Achims Buero Licht umschalten"
by_id["1786612231973"]["alias"] = "DG Achims Schlafzimmer Licht umschalten"

# --- 2. Merge Flur on/off into one toggle automation ---
FLUR_DEVICE_ID = by_id["1734869338637"]["triggers"][0]["device_id"]
FLUR_ENTITIES = by_id["1734869338637"]["actions"][0]["target"]["entity_id"]

flur_merged = {
    "id": str(int(time.time() * 1000)),
    "alias": "DG Flur Licht umschalten",
    "description": "",
    "triggers": [
        {"domain": "mqtt", "device_id": FLUR_DEVICE_ID, "type": "action",
         "subtype": "single", "trigger": "device", "id": "on"},
        {"domain": "mqtt", "device_id": FLUR_DEVICE_ID, "type": "action",
         "subtype": "double", "trigger": "device", "id": "off"},
    ],
    "conditions": [],
    "actions": [
        {"choose": [
            {"conditions": [{"condition": "trigger", "id": "on"}],
             "sequence": [{"action": "light.turn_on", "target": {"entity_id": FLUR_ENTITIES}}]},
            {"conditions": [{"condition": "trigger", "id": "off"}],
             "sequence": [{"action": "light.turn_off", "target": {"entity_id": FLUR_ENTITIES}}]},
        ]},
    ],
    "mode": "single",
}

# --- 3. Merge Wohnzimmer on/off into one toggle automation ---
WZ_DEVICE_ID = by_id["1734869827365"]["triggers"][0]["device_id"]
WZ_ENTITIES = by_id["1734869827365"]["actions"][0]["target"]["entity_id"]

wz_merged = {
    "id": str(int(time.time() * 1000) + 1),
    "alias": "DG Wohnzimmer Licht umschalten",
    "description": "",
    "triggers": [
        {"domain": "mqtt", "device_id": WZ_DEVICE_ID, "type": "action",
         "subtype": "single", "trigger": "device", "id": "on"},
        {"domain": "mqtt", "device_id": WZ_DEVICE_ID, "type": "action",
         "subtype": "double", "trigger": "device", "id": "off"},
    ],
    "conditions": [],
    "actions": [
        {"choose": [
            {"conditions": [{"condition": "trigger", "id": "on"}],
             "sequence": [{"action": "light.turn_on", "target": {"entity_id": WZ_ENTITIES}}]},
            {"conditions": [{"condition": "trigger", "id": "off"}],
             "sequence": [{"action": "light.turn_off", "target": {"entity_id": WZ_ENTITIES}}]},
        ]},
    ],
    "mode": "single",
}

# --- 4. Remove the 4 old on/off automations, add the 2 merged ones ---
REMOVE_IDS = {"1734869338637", "1735015063547", "1734869827365", "1735015557289"}
autos = [a for a in autos if a["id"] not in REMOVE_IDS]
autos.append(flur_merged)
autos.append(wz_merged)

with open(PATH, "w", encoding="utf-8") as f:
    yaml.safe_dump(autos, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

print("flur_merged id:", flur_merged["id"])
print("wz_merged id:", wz_merged["id"])
print("REORGANIZE_DONE")
