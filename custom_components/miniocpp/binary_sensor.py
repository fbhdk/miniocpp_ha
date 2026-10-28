"""Binary sensors for miniocpp."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import PLUGGED_IN_STATUSES
from .coordinator import MiniOcppConfigEntry
from .entity import MiniOcppEntity, async_add_charger_entities, connector_status


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MiniOcppConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the plugged-in binary sensor."""
    async_add_charger_entities(
        entry,
        async_add_entities,
        lambda coordinator, charger_id: [MiniOcppPluggedIn(coordinator, charger_id)],
    )


class MiniOcppPluggedIn(MiniOcppEntity, BinarySensorEntity):
    """A vehicle is connected to the charger."""

    _attr_device_class = BinarySensorDeviceClass.PLUG

    def __init__(self, coordinator, charger_id: str) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, charger_id, "plugged_in")

    @property
    def is_on(self) -> bool:
        """Return true if a vehicle is plugged in."""
        return connector_status(self.snapshot, self.connector) in PLUGGED_IN_STATUSES
