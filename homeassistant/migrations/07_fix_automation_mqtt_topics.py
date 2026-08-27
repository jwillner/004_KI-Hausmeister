import shutil
import time

STAMP = time.strftime("%Y%m%d%H%M%S")
PATH = "/config/automations.yaml"

shutil.copy(PATH, f"{PATH}.bak.{STAMP}")

with open(PATH, encoding="utf-8") as f:
    content = f.read()

REPLACEMENTS = [
    ("zigbee2mqtt/DachAchimsBueroLichtTaster", "zigbee2mqtt/DG Achims Büro Lichttaster"),
    ("zigbee2mqtt/DachAchimsSchlafzimmerLichtschalter", "zigbee2mqtt/DG Achims Schlafzimmer Lichtschalter"),
]

for old, new in REPLACEMENTS:
    count = content.count(old)
    content = content.replace(old, new)
    print(f"replaced {count}x: {old!r} -> {new!r}")

with open(PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("AUTOMATIONS_FIXED")
