"""Diagnostics for miniocpp."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.core import HomeAssistant

from .coordinator import MiniOcppConfigEntry

TO_REDACT = {CONF_API_KEY, CONF_HOST, "unique_id", "id_tag"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: MiniOcppConfigEntry
) -> dict[str, Any]:
    """Return diagnostics with the API key, host (also the unique_id) and RFID tags redacted."""
    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "chargers": async_redact_data(entry.runtime_data.data, TO_REDACT),
    }
