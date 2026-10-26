"""Data update coordinator for miniocpp."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AuthError, CannotConnect, MiniOcppClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

type MiniOcppConfigEntry = ConfigEntry[MiniOcppCoordinator]


class MiniOcppCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Poll all chargers known to the miniocpp server."""

    config_entry: MiniOcppConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: MiniOcppConfigEntry,
        client: MiniOcppClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch charger snapshots, keyed by charger id."""
        try:
            chargers = await self.client.async_get_chargers()
        except AuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except CannotConnect as err:
            raise UpdateFailed(str(err)) from err
        return {charger["id"]: charger for charger in chargers}
