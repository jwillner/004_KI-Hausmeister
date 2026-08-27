import json
import shutil
import time

STAMP = time.strftime("%Y%m%d%H%M%S")
DEVICE_REG = "/config/.storage/core.device_registry"

shutil.copy(DEVICE_REG, f"{DEVICE_REG}.bak.{STAMP}")

with open(DEVICE_REG, encoding="utf-8") as f:
    data = json.load(f)

moved = 0
for dev in data["data"]["devices"]:
    if dev.get("area_id") == "heating":
        dev["area_id"] = "keller"
        moved += 1
        print("moved:", dev.get("name_by_user") or dev.get("name"))

with open(DEVICE_REG, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)

print(f"MOVED {moved} devices to keller")
