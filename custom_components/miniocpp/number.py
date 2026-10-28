"""Charge current limit for miniocpp."""

from __future__ import annotations

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberMode,
    RestoreNumber,
)
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import MiniOcppError
from .const import DEFAULT_MAX_AMPS
from .coordinator import MiniOcppConfigEntry
from .entity import MiniOcppEntity, async_add_charger_entities


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MiniOcppConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the charge current number."""
    async_add_charger_entities(
        entry,
        async_add_entities,
        lambda coordinator, charger_id: [MiniOcppCurrentLimit(coordinator, charger_id)],
    )


class MiniOcppCurrentLimit(MiniOcppEntity, RestoreNumber):
    """Charging current limit. Below 6 A the charger pauses (SuspendedEVSE).

    The API does not report the applied limit, so the last value set from
    Home Assistant is kept and restored across restarts.
    """

    _attr_translation_key = "charge_current"
    _attr_device_class = NumberDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_native_min_value = 0
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator, charger_id: str) -> None:
        """Initialize the number."""
        super().__init__(coordinator, charger_id, "charge_current")
        self._attr_native_value = None

    @property
    def native_max_value(self) -> float:
        """Maximum current reported by the charger."""
        limits = self.snapshot.get("limits") or {}
        return float(limits.get("max_a") or DEFAULT_MAX_AMPS)

    async def async_added_to_hass(self) -> None:
        """Restore the last value set."""
        await super().async_added_to_hass()
        if (last := await self.async_get_last_number_data()) is not None:
            self._attr_native_value = last.native_value

    async def async_set_native_value(self, value: float) -> None:
        """Send the new current limit."""
        try:
            result = await self.coordinator.client.async_set_current(
                self.charger_id, self.connector, value
            )
        except MiniOcppError as err:
            raise HomeAssistantError(f"Setting charge current failed: {err}") from err
        if (status := result.get("status")) != "Accepted":
            raise HomeAssistantError(f"Charger answered {status}")
        self._attr_native_value = float(result.get("amps", value))
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
