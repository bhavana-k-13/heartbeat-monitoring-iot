import json
import time
import uuid
import paho.mqtt.client as mqtt

from app.simulator import next_bpm

BROKER = "broker.hivemq.com"
PORT = 1883

# Separate topic for this project
TOPIC = "iot-heartbeat-demo-2026-11-06-7f3a91/virtual-bpm"

MODE = "mixed"
INTERVAL = 3

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="heartbeat-sensor-" + uuid.uuid4().hex[:8]
)

last_bpm = None

print("Starting Virtual Heartbeat Sensor...")
print("Mode:", MODE)
print("Publishing automatic readings every", INTERVAL, "seconds")

client.connect(BROKER, PORT, 60)
client.loop_start()

try:
    count = 0
    while True:
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
        else:
            print("Publish failed:", result.rc)

        time.sleep(INTERVAL)

except KeyboardInterrupt:
    print("\nVirtual sensor stopped.")

finally:
    client.loop_stop()
    client.disconnect()

