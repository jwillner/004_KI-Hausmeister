import json
import shutil
import time
import uuid

STAMP = time.strftime("%Y%m%d%H%M%S")

AREA_REG = "/config/.storage/core.area_registry"
DEVICE_REG = "/config/.storage/core.device_registry"
LOVELACE = "/config/.storage/lovelace.lovelace"

for path in (AREA_REG, DEVICE_REG, LOVELACE):
    shutil.copy(path, f"{path}.bak.{STAMP}")

# --- 1. Ensure floor areas exist ---
NEW_AREAS = {
    "eg": "EG",
    "dg": "DG",
    "keller": "Keller",
    "aussen": "Außen",
}

with open(AREA_REG, encoding="utf-8") as f:
    area_data = json.load(f)

existing_ids = {a["id"] for a in area_data["data"]["areas"]}
now = time.strftime("%Y-%m-%dT%H:%M:%S.000000+00:00")
for area_id, name in NEW_AREAS.items():
    if area_id not in existing_ids:
        area_data["data"]["areas"].append({
            "aliases": [],
            "floor_id": None,
            "humidity_entity_id": None,
            "icon": None,
            "id": area_id,
            "labels": [],
            "name": name,
            "picture": None,
            "temperature_entity_id": None,
            "created_at": now,
            "modified_at": now,
        })
        print(f"created area: {area_id}")
    else:
        print(f"area already exists: {area_id}")

with open(AREA_REG, "w", encoding="utf-8") as f:
    json.dump(area_data, f, ensure_ascii=False)

# --- 2. Assign devices to floor areas by name prefix ---
PREFIX_MAP = [
    ("EG ", "eg"),
    ("1OG ", "1og"),
    ("DG ", "dg"),
    ("Keller", "keller"),
    ("Außen", "aussen"),
]

with open(DEVICE_REG, encoding="utf-8") as f:
    dev_data = json.load(f)

assigned = 0
skipped = []
for dev in dev_data["data"]["devices"]:
    name = dev.get("name_by_user") or dev.get("name") or ""
    matched = None
    for prefix, area_id in PREFIX_MAP:
        if name.startswith(prefix):
            matched = area_id
            break
    if matched:
        if dev.get("area_id") != matched:
            dev["area_id"] = matched
            assigned += 1
    else:
        skipped.append(name)

with open(DEVICE_REG, "w", encoding="utf-8") as f:
    json.dump(dev_data, f, ensure_ascii=False)

print(f"assigned/updated: {assigned} devices")
print(f"skipped (no floor prefix match): {len(skipped)}")
for n in skipped:
    print("  -", n)

# --- 3. Add a new dashboard view with one area card per floor ---
with open(LOVELACE, encoding="utf-8") as f:
    lov_data = json.load(f)

views = lov_data["data"]["config"]["views"]
if not any(v.get("path") == "nach_etage" for v in views):
    views.append({
        "title": "Nach Etage",
        "path": "nach_etage",
        "icon": "mdi:floor-plan",
        "cards": [
            {"type": "area", "area": "dg"},
            {"type": "area", "area": "1og"},
            {"type": "area", "area": "eg"},
            {"type": "area", "area": "keller"},
            {"type": "area", "area": "aussen"},
        ],
    })
    print("view 'Nach Etage' added")
else:
    print("view 'Nach Etage' already exists, not re-added")

with open(LOVELACE, "w", encoding="utf-8") as f:
    json.dump(lov_data, f, ensure_ascii=False)

print("SETUP_COMPLETE")
