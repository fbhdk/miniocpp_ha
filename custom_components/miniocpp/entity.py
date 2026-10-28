"""Base entity and snapshot helpers for miniocpp."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_CONNECTOR, DOMAIN
from .coordinator import MiniOcppConfigEntry, MiniOcppCoordinator


@callback
def async_add_charger_entities(
    entry: MiniOcppConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
    entities_for: Callable[[MiniOcppCoordinator, str], Iterable[Entity]],
) -> None:
    """Add entities for every charger, including ones that connect later.

    The server only lists connected chargers, so a charger that is offline
    when Home Assistant starts shows up in a later poll.
    """
    coordinator = entry.runtime_data
    known: set[str] = set()

    @callback
    def _add_new_chargers() -> None:
        if not (new := coordinator.data.keys() - known):
            return
        known.update(new)
        async_add_entities(
            entity
            for charger_id in new
            for entity in entities_for(coordinator, charger_id)
        )

    _add_new_chargers()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_chargers))


def connector_status(snapshot: dict[str, Any], connector: int) -> str | None:
    """Return the raw OCPP status of a connector."""
    return snapshot.get("connectors", {}).get(str(connector), {}).get("status")


def meter_reading(
    snapshot: dict[str, Any], connector: int, measurand: str, phase: str | None = None
) -> tuple[float, str] | None:
    """Return (value, unit) of a meter register, or None if not reported.

    Keys are "<measurand>" or "<measurand>@<phase>". Phase may be reported as
    "L1" or "L1-N", so both are accepted.
    """
    meter = snapshot.get("meter", {}).get(str(connector), {})
    if phase is None:
        candidates = [measurand]
    else:
        candidates = [f"{measurand}@{phase}", f"{measurand}@{phase}-N"]
    for key in candidates:
        if (reading := meter.get(key)) is not None and reading.get("value") is not None:
            return float(reading["value"]), reading.get("unit") or ""
    return None


class MiniOcppEntity(CoordinatorEntity[MiniOcppCoordinator]):
    """An entity belonging to one charger connector."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MiniOcppCoordinator,
        charger_id: str,
        key: str,
        connector: int = DEFAULT_CONNECTOR,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.charger_id = charger_id
        self.connector = connector
        self._attr_unique_id = f"{charger_id}_{connector}_{key}"
        boot = self.snapshot.get("boot") or {}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, charger_id)},
            name=charger_id,
            manufacturer=boot.get("vendor") or None,
            model=boot.get("model") or None,
            sw_version=boot.get("firmware_version") or None,
        )

    @property
    def snapshot(self) -> dict[str, Any]:
        """Return the latest snapshot for this charger."""
        return self.coordinator.data.get(self.charger_id, {})

    @property
    def available(self) -> bool:
        """The charger is only listed by the server while it is connected."""
        return super().available and self.charger_id in self.coordinator.data
