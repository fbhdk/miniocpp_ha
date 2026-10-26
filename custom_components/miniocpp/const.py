"""Constants for the miniocpp integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "miniocpp"

DEFAULT_SCAN_INTERVAL: Final = timedelta(seconds=15)
DEFAULT_CONNECTOR: Final = 1
DEFAULT_MAX_AMPS: Final = 32
MIN_CHARGING_AMPS: Final = 6

# OCPP 1.6 ChargePointStatus -> enum sensor option.
# "Unavailable" is mapped to "inoperative" so it can't be confused with
# Home Assistant's own "unavailable" entity state.
CONNECTOR_STATUS: Final = {
    "Available": "available",
    "Preparing": "preparing",
    "Charging": "charging",
    "SuspendedEV": "suspended_ev",
    "SuspendedEVSE": "suspended_evse",
    "Finishing": "finishing",
    "Reserved": "reserved",
    "Unavailable": "inoperative",
    "Faulted": "faulted",
}

# Statuses where a vehicle is connected to the charger.
PLUGGED_IN_STATUSES: Final = frozenset(
    {"Preparing", "Charging", "SuspendedEV", "SuspendedEVSE", "Finishing"}
)
