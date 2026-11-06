import json
import time
import uuid
import threading
import logging
import paho.mqtt.client as mqtt

from app.simulator import next_bpm

BROKER = "broker.hivemq.com"
PORT = 1883

TOPIC = "iot-heartbeat-demo-2026-11-06-7f3a91/virtual-bpm"
CONTROL_TOPIC = "iot-heartbeat-demo-2026-11-06-7f3a91/virtual-bpm/control"

MODE = "mixed"
INTERVAL = 3

running = threading.Event()
running.set()

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="heartbeat-sensor-" + uuid.uuid4().hex[:8]
)

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print("MQTT connection failed:", reason_code)
        return

    print("Connected to MQTT broker!")
    client.subscribe(CONTROL_TOPIC)
    print("Subscribed to control:", CONTROL_TOPIC)

def on_message(client, userdata, message):
    try:
        command = message.payload.decode().strip().upper()

        try:
            data = json.loads(command)
            if isinstance(data, dict):
                command = str(
                    data.get("command", data.get("action", ""))
                ).upper()
        except json.JSONDecodeError:
            pass

        if command in ("STOP", "PAUSE"):
            running.clear()
            print("Virtual sensor STOPPED")

        elif command in ("START", "RESUME"):
            running.set()
            print("Virtual sensor STARTED")

    except Exception:
        logging.exception("Control message error")

client.on_connect = on_connect
client.on_message = on_message

last_bpm = None
count = 0

print("Starting Virtual Heartbeat Sensor...")

client.connect(BROKER, PORT, 60)
client.loop_start()

try:
    while True:
        if running.is_set():
            last_bpm = next_bpm(MODE, last_bpm)
            count += 1

            payload = {
                "device": "virtual_heartbeat_sensor",
                "bpm": last_bpm,
                "reading_number": count,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "simulation": True
            }

            result = client.publish(TOPIC, json.dumps(payload))

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[{count}] Published BPM: {last_bpm}")

        time.sleep(1)

except KeyboardInterrupt:
    print("Virtual sensor stopped.")

finally:
    client.loop_stop()
    client.disconnect()
