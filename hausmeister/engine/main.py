import asyncio
import json
import logging
import os
from datetime import datetime, timezone

import httpx
import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("hausmeister-engine")

MQTT_HOST = os.environ["MQTT_HOST"]
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USERNAME = os.environ["MQTT_USERNAME"]
MQTT_PASSWORD = os.environ["MQTT_PASSWORD"]

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://192.168.1.7:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")

DOOR_OPEN_THRESHOLD_MIN = int(os.environ.get("DOOR_OPEN_THRESHOLD_MIN", "30"))
HEATING_STALE_THRESHOLD_MIN = int(os.environ.get("HEATING_STALE_THRESHOLD_MIN", "30"))
BATTERY_DIGEST_HOUR = int(os.environ.get("BATTERY_DIGEST_HOUR", "8"))
FROST_THRESHOLD_C = float(os.environ.get("FROST_THRESHOLD_C", "10"))
FROST_CLEAR_C = FROST_THRESHOLD_C + 1
OVERHEAT_THRESHOLD_C = float(os.environ.get("OVERHEAT_THRESHOLD_C", "40"))
OVERHEAT_CLEAR_C = OVERHEAT_THRESHOLD_C - 1

DOOR_WINDOW_CLASSES = {"door", "window", "opening", "garage_door"}


def is_room_temperature_sensor(entity_id: str) -> bool:
    """Room/ambient temperature sensors only — excludes heating-bus internals,
    the outdoor sensor, and TRV calibration/config values."""
    if entity_id.startswith("heating_ebusd"):
        return False
    if "aussentemp" in entity_id or "outdoor" in entity_id:
        return False
    if entity_id.endswith(("_calibration", "_external_temperature_input")):
        return False
    return True

entities: dict[str, dict] = {}
heating_last_seen: datetime | None = None
battery_digest_last_sent = None
active_alerts: set[str] = set()


def send_telegram(text: str) -> None:
    try:
        httpx.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=10,
        )
    except Exception:
        log.exception("Failed to send Telegram message")


def ask_ollama(prompt: str) -> str | None:
    try:
        resp = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except Exception:
        log.exception("Ollama request failed")
        return None


def display_name(entity_id: str, rec: dict) -> str:
    return rec.get("friendly_name") or entity_id.replace("_", " ")


def handle_mqtt_message(topic: str, payload: str) -> None:
    parts = topic.split("/")
    if len(parts) != 5:
        return
    _, _, domain, entity_id, attribute = parts
    now = datetime.now(timezone.utc)

    rec = entities.setdefault(entity_id, {"domain": domain})
    rec["last_seen"] = now

    if attribute == "state":
        old_state = rec.get("state")
        rec["state"] = payload
        if old_state != payload:
            rec["state_changed_at"] = now
            on_state_change(entity_id, rec, old_state, payload)
    elif attribute == "device_class":
        try:
            rec["device_class"] = json.loads(payload)
        except (json.JSONDecodeError, TypeError):
            rec["device_class"] = payload
    elif attribute == "friendly_name":
        try:
            rec["friendly_name"] = json.loads(payload)
        except (json.JSONDecodeError, TypeError):
            rec["friendly_name"] = payload

    if entity_id.startswith("heating_ebusd"):
        global heating_last_seen
        was_stale = "heating_bridge" in active_alerts
        heating_last_seen = now
        if was_stale:
            active_alerts.discard("heating_bridge")
            send_telegram("✅ Die Heizungsanbindung (ebusd) meldet wieder Daten.")


def on_state_change(entity_id: str, rec: dict, old_state, new_state) -> None:
    device_class = rec.get("device_class")

    if device_class == "smoke" and new_state == "on":
        name = display_name(entity_id, rec)
        send_telegram(f"🚨 RAUCHALARM: {name} hat Rauch erkannt! Sofort prüfen!")
        enriched = ask_ollama(
            f"Ein Rauchmelder ({name}) im Haus hat gerade ausgelöst. "
            "Schreib in 1-2 kurzen Sätzen auf Deutsch, was der Bewohner jetzt als Erstes tun sollte."
        )
        if enriched:
            send_telegram(f"ℹ️ {enriched}")

    if device_class in DOOR_WINDOW_CLASSES and new_state == "off":
        active_alerts.discard(entity_id)

    if device_class == "temperature" and is_room_temperature_sensor(entity_id):
        try:
            temp = float(new_state)
        except (TypeError, ValueError):
            return
        name = display_name(entity_id, rec)
        frost_key = f"frost:{entity_id}"
        overheat_key = f"overheat:{entity_id}"

        if temp < FROST_THRESHOLD_C and frost_key not in active_alerts:
            active_alerts.add(frost_key)
            send_telegram(
                f"🥶 Frostrisiko: {name} meldet {temp:.1f}°C (unter {FROST_THRESHOLD_C:.0f}°C). "
                "Mögliche Ursache: Heizungsausfall oder offenes Fenster."
            )
        elif temp >= FROST_CLEAR_C:
            active_alerts.discard(frost_key)

        if temp > OVERHEAT_THRESHOLD_C and overheat_key not in active_alerts:
            active_alerts.add(overheat_key)
            send_telegram(
                f"🥵 Überhitzung: {name} meldet {temp:.1f}°C (über {OVERHEAT_THRESHOLD_C:.0f}°C)."
            )
        elif temp <= OVERHEAT_CLEAR_C:
            active_alerts.discard(overheat_key)


async def periodic_checks() -> None:
    global battery_digest_last_sent
    while True:
        await asyncio.sleep(60)
        now = datetime.now(timezone.utc)

        for entity_id, rec in list(entities.items()):
            if (
                rec.get("device_class") in DOOR_WINDOW_CLASSES
                and rec.get("state") == "on"
                and entity_id not in active_alerts
            ):
                changed_at = rec.get("state_changed_at")
                if changed_at and (now - changed_at).total_seconds() / 60 >= DOOR_OPEN_THRESHOLD_MIN:
                    active_alerts.add(entity_id)
                    name = display_name(entity_id, rec)
                    send_telegram(
                        f"🚪 {name} ist seit über {DOOR_OPEN_THRESHOLD_MIN} Minuten offen."
                    )

        if heating_last_seen is not None and "heating_bridge" not in active_alerts:
            stale_minutes = (now - heating_last_seen).total_seconds() / 60
            if stale_minutes >= HEATING_STALE_THRESHOLD_MIN:
                active_alerts.add("heating_bridge")
                send_telegram(
                    "🔥⚠️ Die Heizungsanbindung (ebusd) meldet seit über "
                    f"{HEATING_STALE_THRESHOLD_MIN} Minuten keine Daten mehr. "
                    "Bitte prüfen, ob die Heizungskommunikation noch funktioniert."
                )

        local_now = datetime.now()
        if local_now.hour == BATTERY_DIGEST_HOUR and battery_digest_last_sent != local_now.date():
            low_batteries = [
                display_name(eid, rec)
                for eid, rec in entities.items()
                if rec.get("device_class") == "battery" and rec.get("state") == "on"
            ]
            if low_batteries:
                msg = "🔋 Batteriestatus: Folgende Sensoren melden schwache Batterie:\n" + "\n".join(
                    f"- {n}" for n in low_batteries
                )
                send_telegram(msg)
            battery_digest_last_sent = local_now.date()


def on_connect(client, userdata, flags, rc, properties=None) -> None:
    log.info("Connected to MQTT broker, rc=%s", rc)
    client.subscribe("homeassistant/statestream/#")


def on_message(client, userdata, msg) -> None:
    try:
        payload = msg.payload.decode("utf-8", errors="replace")
        handle_mqtt_message(msg.topic, payload)
    except Exception:
        log.exception("Error handling message on %s", msg.topic)


async def main() -> None:
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()

    log.info("Hausmeister engine started")
    send_telegram("🏠 KI-Hausmeister-Engine ist gestartet und überwacht jetzt das Haus.")

    await periodic_checks()


if __name__ == "__main__":
    asyncio.run(main())
