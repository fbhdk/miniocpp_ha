"""Config flow tests."""

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.data_entry_flow import FlowResultType

from custom_components.miniocpp.const import DOMAIN

from .conftest import API_KEY, HOST, make_snapshot


async def test_user_flow(hass, aioclient_mock):
    """A valid URL and key creates an entry, trailing slash stripped."""
    aioclient_mock.get(f"{HOST}/api/chargers", json=[make_snapshot()])
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: f"{HOST}/", CONF_API_KEY: API_KEY}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_HOST: HOST, CONF_API_KEY: API_KEY}
    assert aioclient_mock.mock_calls[0][3]["X-API-Key"] == API_KEY


async def test_user_flow_invalid_auth(hass, aioclient_mock):
    """A rejected key shows an error."""
    aioclient_mock.get(f"{HOST}/api/chargers", status=401)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_API_KEY: "wrong"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_flow_cannot_connect(hass, aioclient_mock):
    """A server error shows an error."""
    aioclient_mock.get(f"{HOST}/api/chargers", status=500)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_API_KEY: API_KEY}
    )
    assert result["errors"] == {"base": "cannot_connect"}
