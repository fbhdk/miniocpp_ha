# miniocpp for Home Assistant

Control and monitor EV chargers through a miniocpp OCPP 1.6J central system from Home Assistant.

## Installation

### HACS

1. HACS → ⋮ → **Custom repositories** → add `https://github.com/fbhdk/miniocpp_ha`, category **Integration**.
2. Install **miniocpp** and restart Home Assistant.

### Manual

Copy `custom_components/miniocpp` into your `config/custom_components/` folder and restart.

## Configuration

Settings → Devices & Services → **Add integration** → **miniocpp**, then enter:

| Field | Example |
|---|---|
| URL | `http://<host>:8080` |
| API key | `<api-key>` (the value miniocpp expects in the `X-API-Key` header) |

The URL and key are stored only in Home Assistant's config entry. They are never written to YAML. If the key changes, Home Assistant asks for the new one (reauth). To change the URL, use **Reconfigure**.

## Entities

You get one device per connected charger (connector 1):

| Entity | Description |
|---|---|
| Switch **Charging** | Remote start/stop of an OCPP transaction (needs a plugged-in vehicle) |
| Number **Charge current** | Current limit in A. `0`–`5` pauses charging (SuspendedEVSE), `6`+ charges. The last value set is restored after restart |
| Sensor **Status** | Available, Preparing, Charging, Paused by vehicle, Paused by charger, Finishing, Reserved, Unavailable (`inoperative`), Faulted |
| Binary sensor **Plug** | Vehicle connected |
| Sensor **Power** | W |
| Sensor **Energy total** | Lifetime kWh (`total_increasing`). Use this one for the Energy dashboard and utility meters |
| Sensor **Session energy** | kWh for the current session |
| Sensors **Current L1–L3** / **Voltage L1–L3** | Per phase. Voltage sensors are disabled by default |
| Sensor **Last seen** | Last message from the charger (diagnostic) |
| Button **Refresh meter values** | Asks the charger to send MeterValues now (diagnostic) |

The integration polls every 15 seconds. A charger that first connects to miniocpp after the integration is set up appears when you reload the integration.

## Development

```bash
pip install -r requirements.txt -r requirements_test.txt
ruff check . && ruff format --check .
pytest
```
