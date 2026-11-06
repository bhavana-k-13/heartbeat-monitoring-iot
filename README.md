# IoT-Based Heartbeat Monitoring & Stimulation Response System
**Educational software simulation - NOT a medical device.** Thresholds are demo values only.
The "response" is text-only; nothing is stimulated or treated.

## What is implemented (Stage 1, tested)
| Feature | Status |
|---|---|
| Simulated BPM generator (4 modes) + manual BPM input | Done |
| NORMAL / WARNING / CRITICAL classification (demo thresholds) | Done |
| SQLite storage (readings + alerts tables) | Done |
| REST API (send + retrieve data) with input validation | Done |
| Dashboard: live BPM, status, graph, history, stats, alerts | Done |
| Simulated response panel (text only) | Done |
| Separate "IoT device" script sending BPM over REST | Done |
| 13 automated tests | Done (all pass) |
| MQTT messaging | NOT implemented (pending) |
| MySQL / Firebase cloud database | NOT implemented (pending; SQLite used) |
| iFogSim fog/cloud simulation (Java) | Next stage - separate from this app |

## Demo thresholds (BPM)
| Status | Range |
|---|---|
| NORMAL | 60 - 100 |
| WARNING | 50 - 59 or 101 - 120 |
| CRITICAL | below 50 or above 120 |

Inputs outside 20 - 250 are rejected as invalid sensor values. Change values in `app/config.py`.

## Run on Windows 11
1. Install Python 3.10+ from python.org (tick **"Add python.exe to PATH"**).
2. Unzip the project. Open the folder in File Explorer, click the address bar, type `cmd`, press Enter.
3. Create a virtual environment and install Flask:
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
4. Start the server:
```
python run.py
```
Expected: `Running on http://127.0.0.1:5000`. Open that address in your browser.
5. Run tests (new cmd window, same folder, venv activated):
```
python -m unittest discover -s tests -v
```
Expected: `Ran 13 tests ... OK`.
6. Optional device simulator (new cmd window while the server runs):
```
python sensor_simulator.py --count 20 --mode mixed
```

## API
| Method | URL | Purpose |
|---|---|---|
| POST | /api/readings `{"bpm":72}` | Send a reading (201 on success, 400 on bad input) |
| GET | /api/readings?limit=50 | History |
| GET | /api/latest | Latest reading (404 if none) |
| GET | /api/alerts | Recent alerts |
| GET | /api/stats | Totals and averages |
| POST | /api/simulate/next, /start, /stop | One reading / auto mode on / off |
| DELETE | /api/readings | Clear data |

## Common errors
- `'python' is not recognized` -> reinstall Python with "Add to PATH" ticked, reopen cmd.
- `Address already in use` -> another program uses port 5000; close it or change `port=` in `run.py`.
- Scripts blocked in PowerShell -> use **cmd** instead.

## Cloud deployment (Render demo)
This package includes `start.py` to launch the Flask dashboard, MQTT subscriber,
and automatic virtual MQTT sensor in one Render web service.
- Build command: `pip install -r requirements.txt`
- Start command: `python start.py`
- Health check: `/api/health`

Educational simulated-IoT demonstration only; not a medical device. BPM values
are generated in software. No physical sensor or real stimulation is implemented.
The MQTT broker is public (`broker.hivemq.com`); do not send personal or patient data.

Render Free services may sleep after 15 minutes without traffic and take about a
minute to wake. Their local filesystem is ephemeral, so SQLite readings may be
lost on sleep, restart, or redeploy. Continuous availability and durable readings
require an always-on paid service and persistent database.
