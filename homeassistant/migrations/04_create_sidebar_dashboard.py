import json
import shutil
import time

STAMP = time.strftime("%Y%m%d%H%M%S")

LOVELACE_MAIN = "/config/.storage/lovelace.lovelace"
LOVELACE_DASHBOARDS = "/config/.storage/lovelace_dashboards"
LOVELACE_NEW = "/config/.storage/lovelace.nach-etage"

for path in (LOVELACE_MAIN, LOVELACE_DASHBOARDS):
    shutil.copy(path, f"{path}.bak.{STAMP}")

# --- 1. Remove the previously-added tab from the main dashboard ---
with open(LOVELACE_MAIN, encoding="utf-8") as f:
    main_data = json.load(f)

views = main_data["data"]["config"]["views"]
before = len(views)
views[:] = [v for v in views if v.get("path") != "nach_etage"]
removed = before - len(views)

with open(LOVELACE_MAIN, "w", encoding="utf-8") as f:
    json.dump(main_data, f, ensure_ascii=False)

print(f"removed {removed} tab(s) from main dashboard")

# --- 2. Create the new standalone dashboard's storage file ---
new_dashboard_config = {
    "version": 1,
    "minor_version": 1,
    "key": "lovelace.nach-etage",
    "data": {
        "config": {
            "title": "Nach Etage",
            "views": [
                {
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
                }
            ],
        }
    },
}

with open(LOVELACE_NEW, "w", encoding="utf-8") as f:
    json.dump(new_dashboard_config, f, ensure_ascii=False)
print("created lovelace.nach-etage storage file")

# --- 3. Register it as a sidebar dashboard ---
with open(LOVELACE_DASHBOARDS, encoding="utf-8") as f:
    dash_data = json.load(f)

items = dash_data["data"]["items"]
if not any(i.get("id") == "nach-etage" for i in items):
    items.append({
        "id": "nach-etage",
        "icon": "mdi:floor-plan",
        "title": "Nach Etage",
        "url_path": "nach-etage",
        "show_in_sidebar": True,
        "require_admin": False,
        "mode": "storage",
    })
    print("added sidebar entry")
else:
    print("sidebar entry already exists")

with open(LOVELACE_DASHBOARDS, "w", encoding="utf-8") as f:
    json.dump(dash_data, f, ensure_ascii=False)

print("SIDEBAR_SETUP_COMPLETE")
