"""Buttons for miniocpp."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import MiniOcppError
from .coordinator import MiniOcppConfigEntry
from .entity import MiniOcppEntity, async_add_charger_entities


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MiniOcppConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the refresh button."""
    async_add_charger_entities(
        entry,
        async_add_entities,
        lambda coordinator, charger_id: [
            MiniOcppRefreshButton(coordinator, charger_id)
        ],
    )


class MiniOcppRefreshButton(MiniOcppEntity, ButtonEntity):
    """Ask the charger to send fresh meter values."""

    _attr_translation_key = "refresh_meter_values"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, charger_id: str) -> None:
        """Initialize the button."""
        super().__init__(coordinator, charger_id, "refresh_meter_values")

    async def async_press(self) -> None:
        """Trigger a MeterValues message."""
        try:
            await self.coordinator.client.async_trigger(
                self.charger_id, self.connector, "MeterValues"
            )
        except MiniOcppError as err:
            raise HomeAssistantError(f"Trigger failed: {err}") from err
        await self.coordinator.async_request_refresh()
