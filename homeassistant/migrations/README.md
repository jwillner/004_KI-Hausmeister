One-off scripts run directly on the Home Assistant host (192.168.1.30) during the
2026-08-26/27 entity-naming and dashboard cleanup. Kept for reference/reproducibility,
not meant to be re-run as-is (paths, IDs, and credentials are specific to that session).

- `01_zigbee2mqtt_bulk_rename.py` + `01_rename_pairs.tsv` — bulk device rename via the
  Zigbee2MQTT MQTT bridge API (`zigbee2mqtt/bridge/request/device/rename`).
- `02_rename_gas_meter_device.sh` — rename the (non-Zigbee) gas meter device by setting
  `name_by_user` in `core.device_registry` directly.
- `03_create_floor_areas_and_assign_devices.py` — create HA Areas (EG/DG/Keller/Außen;
  1OG already existed) and assign devices to them by parsing the device name prefix.
- `04_create_sidebar_dashboard.py` — add a standalone "Nach Etage" dashboard as its own
  sidebar entry (`lovelace_dashboards` + `lovelace.nach-etage` storage files).
- `05_build_floor_dashboard_cards.py` — populate each floor's card with one representative
  entity per device; final version also injects the dedicated Heizung/Gaszähler detail cards.
- `06_move_heating_devices_to_keller.py` — reassign the ebusd heating devices from the
  pre-existing "Heating" area into "keller".
- `07_fix_automation_mqtt_topics.py` — fix two automations whose raw MQTT triggers
  (`topic: zigbee2mqtt/<old-device-name>`) broke after the device rename in step 01.
- `08_reorganize_automations.py` — rename two automations, merge two on/off automation
  pairs into single toggle automations.
- `09_restore_lost_automation.py` — restore "Hue Dimmer Schlafzimmer", which disappeared
  from `automations.yaml` during a HA restart (root cause unconfirmed).

All scripts that write to `.storage/*` files back up the file first
(`<file>.bak.<timestamp>`) — those backups were left on the HA host, not copied here.
