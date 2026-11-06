"""Run the Flask dashboard plus the simulated MQTT publisher/subscriber."""
import os
import signal
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
children = []
stopping = False

def stop_children(*_):
    global stopping
    stopping = True
    for process in children:
        if process.poll() is None:
            process.terminate()
    for process in children:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

signal.signal(signal.SIGTERM, stop_children)
signal.signal(signal.SIGINT, stop_children)

def launch(script):
    return subprocess.Popen([sys.executable, os.path.join(ROOT, script)], cwd=ROOT)

children.append(launch("mqtt_subscriber.py"))
time.sleep(2)
children.append(launch("virtual_sensor_mqtt.py"))

port = os.environ.get("PORT", "10000")
print(f"Starting Flask/Gunicorn on 0.0.0.0:{port}", flush=True)
web = subprocess.Popen(
    [sys.executable, "-m", "gunicorn", "--workers", "1", "--threads", "4",
     "--bind", f"0.0.0.0:{port}", "run:app"],
    cwd=ROOT,
)
children.append(web)

exit_code = web.wait()
stop_children()
raise SystemExit(exit_code)
