"""Stand-alone 'IoT device' that sends BPM readings to the Flask server over REST.
Run the server first (python run.py), then in a second terminal:
    python sensor_simulator.py --count 20 --mode mixed
Uses only the Python standard library."""
import argparse, json, time, random, urllib.request, urllib.error

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:5000/api/readings")
    p.add_argument("--count", type=int, default=20)
    p.add_argument("--interval", type=float, default=1.0)
    p.add_argument("--mode", choices=["normal", "mixed", "tachycardia", "bradycardia"], default="mixed")
    a = p.parse_args()
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app.simulator import next_bpm
    last = None
    for i in range(a.count):
        last = next_bpm(a.mode, last)
        body = json.dumps({"bpm": last, "source": "device"}).encode()
        req = urllib.request.Request(a.url, body, {"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                d = json.loads(r.read())
                print(f"[{i+1}/{a.count}] sent BPM={last} -> {d['status']}")
        except urllib.error.URLError as e:
            print("Could not reach server. Is 'python run.py' running? ->", e)
            return
        time.sleep(a.interval)

if __name__ == "__main__":
    main()
