"""Threshold classification of a BPM value (demo thresholds, not medical)."""
from . import config as C

NORMAL, WARNING, CRITICAL = "NORMAL", "WARNING", "CRITICAL"


def classify(bpm: int) -> str:
    if bpm < C.WARNING_LOW or bpm > C.WARNING_HIGH:
        return CRITICAL
    if bpm < C.NORMAL_LOW or bpm > C.NORMAL_HIGH:
        return WARNING
    return NORMAL


def describe(bpm: int, status: str) -> str:
    if status == NORMAL:
        return f"BPM {bpm} is inside the demo normal range."
    side = "low" if bpm < C.NORMAL_LOW else "high"
    return f"BPM {bpm} is {side} (demo {status} threshold crossed)."
