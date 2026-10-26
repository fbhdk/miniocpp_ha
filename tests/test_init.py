"""Entity and setup tests."""

from homeassistant.components.diagnostics import REDACTED
from homeassistant.config_entries import ConfigEntryState

from custom_components.miniocpp.diagnostics import async_get_config_entry_diagnostics

from .conftest import API_KEY, CHARGER_ID, HOST, make_snapshot


async def _setup(hass, aioclient_mock, config_entry, snapshot):
    aioclient_mock.get(f"{HOST}/api/chargers", json=[snapshot])
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


async def test_entities_while_charging(hass, aioclient_mock, config_entry):
    """Snapshot values map onto entities with unit conversion."""
    await _setup(hass, aioclient_mock, config_entry, make_snapshot())
    assert config_entry.state is ConfigEntryState.LOADED

    assert hass.states.get("sensor.charger_1_status").state == "charging"
    assert hass.states.get("switch.charger_1_charging").state == "on"
    assert hass.states.get("binary_sensor.charger_1_plug").state == "on"
    assert float(hass.states.get("sensor.charger_1_power").state) == 11000
    assert float(hass.states.get("sensor.charger_1_energy_total").state) == 1004.2
    assert float(hass.states.get("sensor.charger_1_session_energy").state) == 4.2
    assert float(hass.states.get("sensor.charger_1_current_l1").state) == 16.0
    assert hass.states.get("number.charger_1_charge_current").attributes["max"] == 16


async def test_entities_when_idle(hass, aioclient_mock, config_entry):
    """No transaction means switch off; Unavailable maps to inoperative."""
    await _setup(
        hass,
        aioclient_mock,
        config_entry,
        make_snapshot("Unavailable", transaction=False),
    )
    assert hass.states.get("sensor.charger_1_status").state == "inoperative"
    assert hass.states.get("switch.charger_1_charging").state == "off"
    assert hass.states.get("binary_sensor.charger_1_plug").state == "off"
    assert float(hass.states.get("sensor.charger_1_session_energy").state) == 0


async def test_switch_and_number_send_commands(hass, aioclient_mock, config_entry):
    """Switch and number post to the right endpoints."""
    await _setup(hass, aioclient_mock, config_entry, make_snapshot(transaction=False))
    base = f"{HOST}/api/chargers/{CHARGER_ID}"
    aioclient_mock.post(f"{base}/start", json={"status": "Accepted"})
    aioclient_mock.post(f"{base}/current", json={"status": "Accepted", "amps": 10})

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.charger_1_charging"}, blocking=True
    )
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.charger_1_charge_current", "value": 10},
        blocking=True,
    )
    posts = [c for c in aioclient_mock.mock_calls if c[0] == "POST"]
    assert str(posts[0][1]).endswith("/start")
    assert posts[1][2] == {"connector": 1, "amps": 10.0}
    assert float(hass.states.get("number.charger_1_charge_current").state) == 10


async def test_auth_failure_starts_reauth(hass, aioclient_mock, config_entry):
    """401 on setup puts the entry into reauth."""
    aioclient_mock.get(f"{HOST}/api/chargers", status=401)
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.SETUP_ERROR
    assert any(config_entry.async_get_active_flows(hass, {"reauth"}))


async def test_diagnostics_redact_secrets(hass, aioclient_mock, config_entry):
    """Diagnostics never contain the key, host or RFID tags."""
    await _setup(hass, aioclient_mock, config_entry, make_snapshot())
    diag = await async_get_config_entry_diagnostics(hass, config_entry)
    text = str(diag)
    assert API_KEY not in text
    assert "miniocpp.test" not in text
    assert "SECRET-TAG" not in text
    assert diag["entry"]["data"]["api_key"] == REDACTED
