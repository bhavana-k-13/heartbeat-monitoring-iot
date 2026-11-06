import threading
import time
import logging
from flask import Flask, jsonify, request, render_template

def _send_mqtt_control(command):
    # Send START/STOP to the virtual sensor process running in the same host.
    try:
        import paho.mqtt.publish as mqtt_publish
        mqtt_publish.single(
            'iot-heartbeat-demo-2026-11-06-7f3a91/virtual-bpm/control',
            payload=command, hostname='broker.hivemq.com', port=1883,
            client_id='heartbeat-dashboard-control'
        )
        return True
    except Exception as exc:
        logging.getLogger(__name__).warning('Could not send MQTT %s command: %s', command, exc)
        return False

from . import config as C
from . import database as db
from .classifier import classify, describe
from .response import decide_response
from .simulator import next_bpm, MODES

_sim = {"running": False, "mode": "mixed", "interval": C.SIM_INTERVAL_SECONDS}


def parse_bpm(value):
    """Return (int_bpm, None) or (None, error_message)."""
    if isinstance(value, bool):
        return None, "'bpm' must be a number."
    if isinstance(value, (int, float)):
        num = value
    elif isinstance(value, str):
        try:
            num = float(value.strip())
        except ValueError:
            return None, "'bpm' must be a number."
    else:
        return None, "'bpm' must be a number."
    if num != num or num in (float("inf"), float("-inf")):
        return None, "'bpm' must be a finite number."
    bpm = int(round(num))
    if not (C.BPM_MIN_VALID <= bpm <= C.BPM_MAX_VALID):
        return None, f"'bpm' must be between {C.BPM_MIN_VALID} and {C.BPM_MAX_VALID}."
    return bpm, None


def process_reading(bpm, source):
    """Core pipeline: classify -> decide alert/response -> store."""
    status = classify(bpm)
    alert = None
    if status != "NORMAL":
        alert = {"message": describe(bpm, status), "response": decide_response(status)}
    row = db.add_reading(bpm, status, source, alert)
    row["alert"] = alert
    return row


def _sim_loop(app):
    last = None
    while _sim["running"]:
        last = next_bpm(_sim["mode"], last)
        try:
            process_reading(last, "simulator")
        except Exception as exc:  # keep the thread alive
            app.logger.error("simulator error: %s", exc)
        time.sleep(_sim["interval"])


def create_app():
    app = Flask(__name__)
    db.init_db()

    def error(msg, code=400):
        return jsonify({"error": msg}), code

    @app.route("/")
    def dashboard():
        return render_template("dashboard.html", cfg=C)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok",
                        "disclaimer": "Educational simulation, not a medical device."})

    @app.post("/api/readings")
    def post_reading():
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or "bpm" not in data:
            return error("JSON body with a 'bpm' field is required.")
        bpm, err = parse_bpm(data["bpm"])
        if err:
            return error(err)
        source = str(data.get("source", "manual"))[:20]
        return jsonify(process_reading(bpm, source)), 201

    @app.get("/api/readings")
    def list_readings():
        try:
            limit = max(1, min(500, int(request.args.get("limit", 50))))
        except ValueError:
            return error("'limit' must be an integer.")
        return jsonify(db.get_readings(limit))

    @app.get("/api/latest")
    def latest():
        r = db.get_latest()
        if not r:
            return error("no readings yet", 404)
        return jsonify(r)

    @app.get("/api/alerts")
    def alerts():
        return jsonify(db.get_alerts(20))

    @app.get("/api/stats")
    def stats():
        return jsonify(db.get_stats())

    @app.delete("/api/readings")
    def clear():
        db.clear_all()
        return jsonify({"cleared": True})

    @app.post("/api/simulate/next")
    def sim_next():
        mode = (request.get_json(silent=True) or {}).get("mode", "mixed")
        if mode not in MODES:
            return error(f"mode must be one of {list(MODES)}")
        last = db.get_latest()
        bpm = next_bpm(mode, last["bpm"] if last else None)
        return jsonify(process_reading(bpm, "simulator")), 201

    @app.post("/api/simulate/start")
    def sim_start():
        mode = (request.get_json(silent=True) or {}).get("mode", "mixed")
        if mode not in MODES:
            return error(f"mode must be one of {list(MODES)}")
        _sim["mode"] = mode
        mqtt_ok = _send_mqtt_control("START")
        if not _sim["running"]:
            _sim["running"] = True
            threading.Thread(target=_sim_loop, args=(app,), daemon=True).start()
        return jsonify({"running": True, "mode": mode, "mqtt_sensor_command_sent": mqtt_ok})

    @app.post("/api/simulate/stop")
    def sim_stop():
        _sim["running"] = False
        mqtt_ok = _send_mqtt_control("STOP")
        return jsonify({"running": False, "mqtt_sensor_command_sent": mqtt_ok})

    @app.get("/api/simulate/status")
    def sim_status():
        return jsonify({"running": _sim["running"], "mode": _sim["mode"]})

    return app
