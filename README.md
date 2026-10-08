# ArkSignal Weather for Home Assistant

Puts your weather station on the [ArkSignal](https://arksignal.allisononline.org) weather map. Home Assistant reads your station as it always has; this integration sends a copy of its readings to your **private ArkSignal upload address** once a minute. You pick the device, it finds the right sensors, and that is the whole setup.

Works with any weather device Home Assistant has: Tempest (WeatherFlow), Ecowitt, Ambient Weather, Davis, Netatmo, a `weather` entity, or sensors you built yourself.

## Install (HACS)

1. On ArkSignal open **My Weather Stations**, add a station and choose *Home Assistant, a Tempest bridge or a script*. Copy its upload address (it looks like `http://host/wx/relay/` followed by a long secret).
2. In Home Assistant open **HACS, Custom repositories**, add this repository as an **Integration**, then download **ArkSignal Weather** and restart Home Assistant. HACS tells you when a new version is out.
3. **Settings, Devices & services, Add integration, ArkSignal Weather.** Paste the upload address, choose your weather station's device, check the sensors it found, finish.

Change the sensors or how often it sends (default every 60 seconds) later with the integration's **Configure** button.

## What is sent

For each value you chose: the number and the unit Home Assistant shows for it (for example `{"temperature": {"value": 21.5, "unit": "°C"}}`). ArkSignal converts, so metric and imperial sensors both work. Values that are unavailable are skipped. The values are temperature, humidity, sea-level pressure, wind speed, wind gust, wind direction, rain today, rain rate, solar radiation, UV index, dew point, lightning strikes and lightning distance. If your station only gives a `weather` entity, choose it and it fills in whatever the sensors do not.

Nothing else leaves Home Assistant: no names, locations or account details. Where the station appears and how precisely is decided in ArkSignal (General, Exact or Hidden), and it is only public if you tick that box there.

## Tempest without Home Assistant

See [`bridge/`](bridge/): a small program (and a ready-made container, `ghcr.io/mallison01/arksignal-tempest-bridge`) that listens to the Tempest hub's local broadcast and sends the same readings.

## Tests

* `python3 tests/test_mapping.py`: how sensors are recognised and the payload is built (plain Python).
* `tests/ha/`: a fake Tempest device and instructions to run the integration inside a real Home Assistant container and drive its setup through Home Assistant's own API.
* `python3 bridge/test_bridge.py`: the Tempest bridge.

## Releases

HACS reads the version from the release tag, which must match `version` in `custom_components/arksignal/manifest.json`. Pushing a `v*` tag also builds and publishes the Tempest bridge container.

## Licence

MIT, see [LICENSE](LICENSE).
