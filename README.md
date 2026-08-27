# KI-Hausmeister

A local, self-hosted "AI caretaker" for the house: a home-monitoring and alerting
system built on top of an existing Home Assistant installation, not a chatbot app.

Home Assistant (running on a separate machine) publishes all entity state changes to
MQTT. A small stack on `kipc` — a local Ubuntu server with a GPU — ingests that stream,
stores it as time series, watches for a handful of concrete anomalies (smoke alarm,
doors/windows left open, frost/overheat, low batteries, a stalled heating bus), and
sends alerts to Telegram. A local LLM (via [Ollama](https://ollama.com)) is used only
to phrase/enrich alert messages — never to decide *whether* to alert.

## Architecture

```
Home Assistant (separate machine, 192.168.1.30)
  └─ mqtt_statestream → Mosquitto broker
                              │
                              ▼
kipc (192.168.1.7, Ubuntu Server + Docker + NVIDIA GPU)
  ├─ Telegraf        → subscribes to MQTT, writes to InfluxDB
  ├─ InfluxDB 2.7     → time-series storage (org "hausmeister", bucket "sensors")
  ├─ hausmeister-engine → subscribes to MQTT directly, applies rules, calls Ollama
  │                        for wording, sends Telegram alerts
  ├─ telegram-bot     → Telegram bot (/start, /status), receives commands
  └─ Ollama (host, not containerized) → local LLM (llama3.2:3b), GPU-accelerated
```

## Repository layout

- `hausmeister/` — the Docker Compose stack that runs on kipc (InfluxDB, Telegraf,
  the rule engine, the Telegram bot). Copy `.env.example` to `.env` and fill in
  credentials before running `docker compose up -d`.
- `homeassistant/migrations/` — one-off scripts run directly on the Home Assistant
  host during the 2026-08 entity-naming/dashboard/automation cleanup. Reference only,
  not meant to be re-run as-is — see that folder's own README.
- `docs/entity-rename.html` — a working checklist used to rename ~45 Home Assistant
  devices to a consistent `{Etage} {Raum} {Gerätetyp}` naming scheme.

## Rule engine (`hausmeister/engine`)

Rules key off Home Assistant's `device_class` metadata (not hardcoded entity names),
so new sensors of an already-handled type work automatically:

| Rule | Trigger | Notes |
|---|---|---|
| Smoke alarm | `device_class: smoke` → `on` | Immediate alert, LLM wording follows async |
| Door/window open | `device_class` door/window/opening/garage_door open > `DOOR_OPEN_THRESHOLD_MIN` | Default 30 min |
| Heating bridge stale | no `heating_ebusd_*` MQTT message for > `HEATING_STALE_THRESHOLD_MIN` | No reliable per-fault-code field exists in the raw ebusd data; this only checks the bridge is alive |
| Frost / overheat | `device_class: temperature` outside `FROST_THRESHOLD_C`–`OVERHEAT_THRESHOLD_C` | Excludes heating-bus internals, the outdoor sensor, and TRV calibration values |
| Low battery | `device_class: battery` | Daily digest at `BATTERY_DIGEST_HOUR`, not per-sensor spam |

## Status

See the project scope memory for the full, up-to-date status — this README covers
the shape of the thing, not a running log. Not yet built: a REST API/dashboard layer
beyond the rule engine itself, and camera/Frigate integration.
