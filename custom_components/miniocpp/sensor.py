"""Sensors for miniocpp."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import CONNECTOR_STATUS
from .coordinator import MiniOcppConfigEntry
from .entity import MiniOcppEntity, connector_status, meter_reading


def _scaled(
    measurand: str, base_unit: str, phase: str | None = None
) -> Callable[[dict[str, Any], int], float | None]:
    """Read a meter register and convert k-prefixed units to the base unit."""

    def value(snapshot: dict[str, Any], connector: int) -> float | None:
        if (reading := meter_reading(snapshot, connector, measurand, phase)) is None:
            return None
        number, unit = reading
        if unit.lower() == f"k{base_unit}".lower():
            return number * 1000
        return number

    return value


def _energy_total(snapshot: dict[str, Any], connector: int) -> float | None:
    if (
        wh := _scaled("Energy.Active.Import.Register", "Wh")(snapshot, connector)
    ) is None:
        return None
    return round(wh / 1000, 3)


def _session_energy(snapshot: dict[str, Any], connector: int) -> float | None:
    session = snapshot.get("session", {}).get(str(connector))
    if not session or session.get("energy_wh") is None:
        return 0.0
    return round(float(session["energy_wh"]) / 1000, 3)


def _status(snapshot: dict[str, Any], connector: int) -> str | None:
    return CONNECTOR_STATUS.get(connector_status(snapshot, connector) or "")


def _last_seen(snapshot: dict[str, Any], connector: int) -> datetime | None:
    if not (ts := snapshot.get("last_seen")):
        return None
    return dt_util.parse_datetime(ts)


@dataclass(frozen=True, kw_only=True)
class MiniOcppSensorEntityDescription(SensorEntityDescription):
    """Describes a miniocpp sensor."""

    value_fn: Callable[[dict[str, Any], int], Any]


SENSORS: tuple[MiniOcppSensorEntityDescription, ...] = (
    MiniOcppSensorEntityDescription(
        key="status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=list(CONNECTOR_STATUS.values()),
        value_fn=_status,
    ),
    MiniOcppSensorEntityDescription(
        key="power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=_scaled("Power.Active.Import", "W"),
    ),
    MiniOcppSensorEntityDescription(
        key="energy_total",
        translation_key="energy_total",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        value_fn=_energy_total,
    ),
    MiniOcppSensorEntityDescription(
        key="session_energy",
        translation_key="session_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        value_fn=_session_energy,
    ),
    *(
        MiniOcppSensorEntityDescription(
            key=f"current_{phase.lower()}",
            translation_key="current_phase",
            translation_placeholders={"phase": phase},
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            suggested_display_precision=1,
            value_fn=_scaled("Current.Import", "A", phase),
        )
        for phase in ("L1", "L2", "L3")
    ),
    *(
        MiniOcppSensorEntityDescription(
            key=f"voltage_{phase.lower()}",
            translation_key="voltage_phase",
            translation_placeholders={"phase": phase},
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            suggested_display_precision=0,
            entity_registry_enabled_default=False,
            value_fn=_scaled("Voltage", "V", phase),
        )
        for phase in ("L1", "L2", "L3")
    ),
    MiniOcppSensorEntityDescription(
        key="last_seen",
        translation_key="last_seen",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_last_seen,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MiniOcppConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up miniocpp sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        MiniOcppSensor(coordinator, charger_id, description)
        for charger_id in coordinator.data
        for description in SENSORS
    )


class MiniOcppSensor(MiniOcppEntity, SensorEntity):
    """A miniocpp sensor."""

    entity_description: MiniOcppSensorEntityDescription

    def __init__(
        self,
        coordinator,
        charger_id: str,
        description: MiniOcppSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, charger_id, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.snapshot, self.connector)
