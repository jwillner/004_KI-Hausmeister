#!/usr/bin/env python3
import json
import subprocess
import sys
import time

HOST = "192.168.1.30"
USER = "mqtt_kipc"
PW = "85268526"
REQ_TOPIC = "zigbee2mqtt/bridge/request/device/rename"
RESP_TOPIC = "zigbee2mqtt/bridge/response/device/rename"

pairs = []
with open("rename_batch.tsv", encoding="utf-8") as f:
    for line in f:
        line = line.rstrip("\n")
        if not line.strip():
            continue
        old, new = line.split("\t")
        pairs.append((old, new))

results = []
for old, new in pairs:
    sub = subprocess.Popen(
        [
            "mosquitto_sub", "-h", HOST, "-p", "1883", "-u", USER, "-P", PW,
            "-t", RESP_TOPIC, "-C", "1", "-W", "5",
        ],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
    )
    time.sleep(0.3)
    payload = json.dumps({"from": old, "to": new}, ensure_ascii=False)
    subprocess.run(
        [
            "mosquitto_pub", "-h", HOST, "-p", "1883", "-u", USER, "-P", PW,
            "-t", REQ_TOPIC, "-m", payload,
        ],
        check=False,
    )
    out, _ = sub.communicate(timeout=8)
    out = out.strip()
    status = "TIMEOUT"
    error = ""
    if out:
        try:
            resp = json.loads(out)
            status = resp.get("status", "?")
            error = resp.get("error", "")
        except json.JSONDecodeError:
            status = "PARSE_ERROR"
            error = out
    results.append((old, new, status, error))
    print(f"{status:10s} {old!r} -> {new!r}" + (f"  [{error}]" if error else ""))
    time.sleep(0.4)

ok = sum(1 for r in results if r[2] == "ok")
print(f"\n{ok}/{len(results)} erfolgreich")
failures = [r for r in results if r[2] != "ok"]
if failures:
    print("Fehlgeschlagen:")
    for old, new, status, error in failures:
        print(f"  {status}: {old!r} -> {new!r} {error}")
