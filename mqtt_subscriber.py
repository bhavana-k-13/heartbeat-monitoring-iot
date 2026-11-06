import json
import logging
import paho.mqtt.client as mqtt

from app import create_app, process_reading, parse_bpm

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "iot-heartbeat-demo-2026-11-06-7f3a91/virtual-bpm"

logging.basicConfig(level=logging.INFO)

app = create_app()

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print("MQTT connection failed:", reason_code)
        return

    print("Connected to MQTT broker!")
    client.subscribe(TOPIC)
    print("Subscribed to:", TOPIC)

def on_message(client, userdata, message):
    try:
        data = json.loads(message.payload.decode())
        bpm, error = parse_bpm(data.get("bpm"))

        if error:
            print("Invalid reading:", error)
            return

        with app.app_context():
            result = process_reading(bpm, "mqtt_virtual_sensor")

        print(
            f"MQTT received BPM={bpm} | "
            f"Status={result['status']} | Saved to database"
        )

    except Exception as exc:
        logging.exception("Error processing MQTT message: %s", exc)

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="heartbeat-flask-subscriber"
)

client.on_connect = on_connect
client.on_message = on_message

print("Starting MQTT subscriber...")
client.connect(BROKER, PORT, 60)
client.loop_forever()

