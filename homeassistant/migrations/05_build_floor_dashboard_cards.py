import json
import shutil
import time

STAMP = time.strftime("%Y%m%d%H%M%S")
LOVELACE_NEW = "/config/.storage/lovelace.nach-etage"

with open("/config/.storage/core.device_registry", encoding="utf-8") as f:
    devices = json.load(f)["data"]["devices"]

with open("/config/.storage/core.entity_registry", encoding="utf-8") as f:
    entities = json.load(f)["data"]["entities"]

by_device = {}
for e in entities:
    by_device.setdefault(e.get("device_id"), []).append(e)

DOMAIN_PRIORITY = ["light", "switch", "climate", "binary_sensor", "cover", "sensor"]
DIAGNOSTIC_HINTS = ("battery", "voltage", "linkquality", "current", "energy", "power", "child_lock",
                    "identify", "countdown", "indicator", "outage", "protect", "overload",
                    "network", "power_on_behavior", "tamper")

# These get their own dedicated detail card (copied from the main dashboard) instead of a
# single summary row in the general device list.
DETAIL_CARD_DEVICES = {"ebusd bai", "ebusd", "ebusd eBUS device", "Smartnetz Gasreader Gasreader"}

HEIZUNG_CARD = {
    "type": "entities",
    "title": "Heizung",
    "entities": [
        {"entity": "sensor.heating_ebusd_bai_flowtemp_temp", "name": "Vorlauf Ist"},
        {"entity": "sensor.heating_ebusd_bai_expertlevel_returntemp_temp", "name": "Rücklauf Ist"},
        {"entity": "sensor.heating_ebusd_bai_flowtempdesired", "name": "Vorlauf Soll"},
        {"entity": "sensor.heating_ebusd_bai_flowtempmax", "name": "Vorlauf Max"},
        {"entity": "sensor.heating_ebusd_bai_outdoorstempsensor_temp", "name": "Außentemperatur"},
        {"entity": "sensor.heating_ebusd_bai_hcpumpmode", "name": "Heizkreis-Pumpe"},
        {"entity": "sensor.heating_ebusd_bai_hcstarts", "name": "Heizkreis-Starts (gesamt)"},
        {"entity": "sensor.heating_ebusd_bai_hcunderhundredstarts", "name": "Kurztakt-Starts (<100s)"},
    ],
}

GASZAEHLER_CARD = {
    "type": "entities",
    "title": "Keller Gaszaehler",
    "entities": [
        {"entity": "sensor.smartnetz_gasreader_gasreader_verbrauch_energie_gestern", "name": "Verbrauch Energie gestern"},
        {"entity": "sensor.smartnetz_gasreader_gasreader_verbrauch_energie_heute", "name": "Verbrauch Energie heute"},
        {"entity": "sensor.smartnetz_gasreader_gasreader_verbrauch_energie_vorgestern", "name": "Verbrauch Energie vorgestern"},
        {"entity": "sensor.smartnetz_gasreader_gasreader_verbrauch_volumen_gestern", "name": "Verbrauch Volumen gestern"},
        {"entity": "sensor.smartnetz_gasreader_gasreader_verbrauch_volumen_heute", "name": "Verbrauch Volumen heute"},
        {"entity": "sensor.smartnetz_gasreader_gasreader_verbrauch_volumen_vorgestern", "name": "Verbrauch Volumen vorgestern"},
        {"entity": "sensor.smartnetz_gasreader_gasreader_zahlerstand", "name": "Zählerstand"},
        {"entity": "sensor.smartnetz_gasreader_gasreader_zahlung_seit_nullung", "name": "Zählung seit Nullung"},
    ],
}

FLOOR_AREAS = ["dg", "1og", "eg", "keller", "aussen"]
FLOOR_TITLES = {"dg": "DG", "1og": "1OG", "eg": "EG", "keller": "Keller", "aussen": "Außen"}

def pick_entities(dev):
    dev_id = dev.get("id")
    dev_name = dev.get("name_by_user") or dev.get("name") or ""
    ents = by_device.get(dev_id, [])

    if dev_name in DETAIL_CARD_DEVICES:
        return []  # covered by a dedicated detail card instead

    for domain in DOMAIN_PRIORITY:
        for e in ents:
            eid = e.get("entity_id", "")
            if not eid.startswith(domain + "."):
                continue
            if e.get("entity_category") == "diagnostic":
                continue
            if any(h in eid for h in DIAGNOSTIC_HINTS):
                continue
            return [eid]  # one representative entity per device
    return []

cards = []
for area in FLOOR_AREAS:
    area_devices = [d for d in devices if d.get("area_id") == area]
    area_devices.sort(key=lambda d: d.get("name_by_user") or d.get("name") or "")
    entity_rows = []
    for dev in area_devices:
        entity_rows.extend(pick_entities(dev))
    cards.append({
        "type": "entities",
        "title": FLOOR_TITLES[area],
        "entities": entity_rows,
        "show_header_toggle": False,
    })
    if area == "keller":
        cards.append(HEIZUNG_CARD)
        cards.append(GASZAEHLER_CARD)
    print(f"{area}: {len(area_devices)} devices -> {len(entity_rows)} entity rows")

with open(LOVELACE_NEW, encoding="utf-8") as f:
    dash = json.load(f)
shutil.copy(LOVELACE_NEW, f"{LOVELACE_NEW}.bak.{STAMP}")

dash["data"]["config"]["views"][0]["cards"] = cards
dash["data"]["config"]["views"][0]["type"] = "masonry"

with open(LOVELACE_NEW, "w", encoding="utf-8") as f:
    json.dump(dash, f, ensure_ascii=False)

print("CARDS_BUILT")
