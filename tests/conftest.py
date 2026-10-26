"""Fixtures for miniocpp tests. All hosts, ids and keys here are fake."""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.const import CONF_API_KEY, CONF_HOST
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.miniocpp.const import DOMAIN

HOST = "http://miniocpp.test:8080"
API_KEY = "test-key"
CHARGER_ID = "charger-1"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations."""
    return


def make_snapshot(status: str = "Charging", transaction: bool = True) -> dict[str, Any]:
    """Return a charger snapshot shaped like GET /api/chargers."""
    return {
        "id": CHARGER_ID,
        "profile": "generic",
        "boot": {"vendor": "Acme", "model": "Wallbox", "firmware_version": "1.2.3"},
        "connectors": {
            "0": {
                "status": "Available",
                "error_code": "NoError",
                "ts": "2026-01-01T00:00:00Z",
            },
            "1": {
                "status": status,
                "error_code": "NoError",
                "ts": "2026-01-01T00:00:00Z",
            },
        },
        "transactions": {"1": 42} if transaction else {},
        "session": (
            {
                "1": {
                    "tx": 42,
                    "id_tag": "SECRET-TAG",
                    "meter_start": 1000000,
                    "started_at": "2026-01-01T00:00:00Z",
                    "energy_wh": 4200,
                }
            }
            if transaction
            else {}
        ),
        "meter": {
            "1": {
                "Energy.Active.Import.Register": {
                    "value": 1004200,
                    "unit": "Wh",
                    "ts": "2026-01-01T00:00:00Z",
                },
                "Power.Active.Import": {
                    "value": 11.0,
                    "unit": "kW",
                    "ts": "2026-01-01T00:00:00Z",
                },
                "Current.Import@L1": {
                    "value": 16.0,
                    "unit": "A",
                    "ts": "2026-01-01T00:00:00Z",
                },
                "Current.Import@L2": {
                    "value": 15.9,
                    "unit": "A",
                    "ts": "2026-01-01T00:00:00Z",
                },
                "Current.Import@L3": {
                    "value": 16.1,
                    "unit": "A",
                    "ts": "2026-01-01T00:00:00Z",
                },
                "Voltage@L1-N": {
                    "value": 230.0,
                    "unit": "V",
                    "ts": "2026-01-01T00:00:00Z",
                },
            }
        },
        "last_seen": "2026-01-01T00:00:00+00:00",
        "limits": {"min_a": 6, "max_a": 16},
    }


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="miniocpp",
        unique_id=HOST,
        data={CONF_HOST: HOST, CONF_API_KEY: API_KEY},
    )
