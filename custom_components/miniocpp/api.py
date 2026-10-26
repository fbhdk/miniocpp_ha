"""Async client for the miniocpp REST API."""

from __future__ import annotations

from typing import Any

import aiohttp

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)


class MiniOcppError(Exception):
    """Base error for the miniocpp client."""


class CannotConnect(MiniOcppError):
    """The server could not be reached or returned an error."""


class AuthError(MiniOcppError):
    """The API key was rejected."""


class MiniOcppClient:
    """Thin wrapper around the miniocpp REST API."""

    def __init__(self, session: aiohttp.ClientSession, host: str, api_key: str) -> None:
        """Initialize the client."""
        self._session = session
        self._host = host.rstrip("/")
        self._api_key = api_key

    async def _request(
        self, method: str, path: str, json: dict[str, Any] | None = None
    ) -> Any:
        """Send a request and return the decoded JSON body."""
        try:
            async with self._session.request(
                method,
                f"{self._host}{path}",
                headers={"X-API-Key": self._api_key},
                json=json,
                timeout=REQUEST_TIMEOUT,
            ) as resp:
                if resp.status in (401, 403):
                    raise AuthError("API key rejected")
                if resp.status >= 400:
                    raise CannotConnect(f"{method} {path} returned HTTP {resp.status}")
                return await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise CannotConnect(f"{method} {path} failed: {err}") from err

    async def async_get_chargers(self) -> list[dict[str, Any]]:
        """Return snapshots of all connected chargers."""
        return await self._request("GET", "/api/chargers")

    async def async_start(self, charger_id: str, connector: int) -> dict[str, Any]:
        """Remote-start a charging session."""
        return await self._request(
            "POST", f"/api/chargers/{charger_id}/start", {"connector": connector}
        )

    async def async_stop(self, charger_id: str, connector: int) -> dict[str, Any]:
        """Remote-stop the active charging session."""
        return await self._request(
            "POST", f"/api/chargers/{charger_id}/stop", {"connector": connector}
        )

    async def async_set_current(
        self, charger_id: str, connector: int, amps: float
    ) -> dict[str, Any]:
        """Set the charging current limit. Below 6 A pauses charging."""
        return await self._request(
            "POST",
            f"/api/chargers/{charger_id}/current",
            {"connector": connector, "amps": amps},
        )

    async def async_trigger(
        self, charger_id: str, connector: int, message: str
    ) -> dict[str, Any]:
        """Ask the charger to send a message (e.g. MeterValues) now."""
        return await self._request(
            "POST",
            f"/api/chargers/{charger_id}/trigger",
            {"connector": connector, "message": message},
        )
