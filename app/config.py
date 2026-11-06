"""Configuration for the Heartbeat Monitoring demo.
All thresholds are DEMONSTRATION values only - NOT medical criteria."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("HEARTBEAT_DB", os.path.join(BASE_DIR, "..", "heartbeat.db"))

# Accepted input range. Anything outside is rejected as a bad sensor value.
BPM_MIN_VALID = 20
BPM_MAX_VALID = 250

# Demo thresholds (BPM)
NORMAL_LOW = 60
NORMAL_HIGH = 100
WARNING_LOW = 50     # 50-59 -> WARNING, below 50 -> CRITICAL
WARNING_HIGH = 120   # 101-120 -> WARNING, above 120 -> CRITICAL

SIM_INTERVAL_SECONDS = 2.0
