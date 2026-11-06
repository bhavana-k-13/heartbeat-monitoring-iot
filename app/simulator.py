"""Software heartbeat simulator (stands in for a physical sensor)."""
import random

MODES = ("normal", "mixed", "tachycardia", "bradycardia")


def next_bpm(mode: str = "mixed", last=None) -> int:
    if mode == "normal":
        base = random.gauss(75, 6)
        if last is not None:
            base = 0.6 * base + 0.4 * last
    elif mode == "tachycardia":
        base = random.gauss(135, 10)
    elif mode == "bradycardia":
        base = random.gauss(44, 4)
    else:  # mixed: mostly normal, occasional abnormal spikes
        r = random.random()
        if r < 0.70:
            base = random.gauss(75, 8)
        elif r < 0.85:
            base = random.choice([random.gauss(110, 5), random.gauss(55, 2)])
        else:
            base = random.choice([random.gauss(135, 8), random.gauss(44, 3)])
    return int(max(20, min(250, round(base))))
