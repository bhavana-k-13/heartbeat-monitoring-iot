"""Simulated response logic. This only returns TEXT describing what a real
system might do. It does NOT control any hardware or deliver stimulation."""
from .classifier import WARNING, CRITICAL


def decide_response(status: str):
    if status == CRITICAL:
        return ("SIMULATED: escalate to emergency contact and log a "
                "simulated stimulation-response event (no real stimulation)")
    if status == WARNING:
        return "SIMULATED: notify caregiver and increase sampling frequency"
    return None
