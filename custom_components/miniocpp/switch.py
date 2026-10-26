"""Charging start/stop switch for miniocpp."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import MiniOcppError
from .coordinator import MiniOcppConfigEntry
from .entity import MiniOcppEntity

ACCEPTED = "Accepted"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MiniOcppConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the charging switch."""
    coordinator = entry.runtime_data
    async_add_entities(
        MiniOcppChargingSwitch(coordinator, charger_id)
        for charger_id in coordinator.data
    )


class MiniOcppChargingSwitch(MiniOcppEntity, SwitchEntity):
    """Start or stop an OCPP transaction."""

    _attr_translation_key = "charging"

    def __init__(self, coordinator, charger_id: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, charger_id, "charging")

    @property
    def is_on(self) -> bool:
        """A transaction is active on the connector."""
        return str(self.connector) in self.snapshot.get("transactions", {})

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Remote-start a session."""
        await self._send(self.coordinator.client.async_start)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Remote-stop the session."""
        await self._send(self.coordinator.client.async_stop)

    async def _send(self, command) -> None:
        try:
            result = await command(self.charger_id, self.connector)
        except MiniOcppError as err:
            raise HomeAssistantError(f"Charger command failed: {err}") from err
        await self.coordinator.async_request_refresh()
        if (status := result.get("status")) != ACCEPTED:
            raise HomeAssistantError(f"Charger answered {status}")
