<p align="center">
  <img src="https://raw.githubusercontent.com/mallison01/arksignal-homeassistant/main/images/banner.png" alt="ArkSignal Weather for Home Assistant" width="640">
</p>

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=mallison01&repository=arksignal-homeassistant&category=integration"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Add to HACS"></a>
  <a href="https://my.home-assistant.io/redirect/config_flow_start/?domain=arksignal"><img src="https://my.home-assistant.io/badges/config_flow_start.svg" alt="Add the integration"></a>
  <br>
  <img src="https://img.shields.io/github/v/release/mallison01/arksignal-homeassistant?style=flat-square&color=3ee6a8" alt="Release">
  <img src="https://img.shields.io/badge/HACS-custom-41bdf5?style=flat-square" alt="HACS custom repository">
  <img src="https://img.shields.io/github/license/mallison01/arksignal-homeassistant?style=flat-square" alt="MIT license">
</p>

# Put your weather station on the ArkSignal map

[ArkSignal](https://arksignal.allisononline.org) is Arkansas's open network for what is overhead, outdoors and on the air. This integration sends your weather station's readings to your own private ArkSignal station once a minute, so it shows up on the weather map next to everyone else's, with live conditions, charts, daily summaries and records.

You pick the device, it finds the right sensors by itself. That is the whole setup.

**Works with** Tempest (WeatherFlow), Ecowitt, Ambient Weather, Davis, Netatmo, any `weather` entity, or sensors you built yourself: if Home Assistant has it, ArkSignal can show it. Tempest owners without Home Assistant can use the [Tempest bridge](bridge/) instead.

---

## Install

**1. Make your station on ArkSignal.** Open **My Weather Stations**, add a station, and choose *Home Assistant, a Tempest bridge or a script*. Copy its **upload address** (it looks like `http://host/wx/relay/` followed by a long secret).

**2. Add this repository to HACS.** Click the *Add to HACS* button above, or in HACS open **Custom repositories** and add `https://github.com/mallison01/arksignal-homeassistant` as an **Integration**. Download **ArkSignal Weather** and restart Home Assistant. HACS tells you when a new version is out.

**3. Add the integration.** Click *Add the integration* above, or go to **Settings, Devices & services, Add integration, ArkSignal Weather**, then:

| Step | What you do |
|---|---|
| Upload address | Paste the address from ArkSignal. It is checked on the spot. |
| Device | Choose your weather station's device. |
| Sensors | Check what was found. Change or clear any of them. |

Change the sensors or how often it sends (default 60 seconds) any time with the integration's **Configure** button.

---

## What is sent

| Value | Notes |
|---|---|
| Temperature, dew point | any unit |
| Humidity | % |
| Pressure | use the sea-level sensor if you have both |
| Wind speed, gust, direction | any speed unit; direction in degrees |
| Rain today, rain rate | mm or inches |
| Solar radiation, UV index | W/m², index |
| Lightning strikes, distance | if your station has a lightning sensor |

Every value goes with the unit Home Assistant shows for it, and ArkSignal converts, so metric and imperial sensors both work. Unavailable values are skipped. If your station only gives a `weather` entity, choose it and it fills in whatever the sensors do not.

## Privacy

Nothing else leaves Home Assistant: no names, locations or account details. Whether your station is public, and how precisely its position is shown (General, Exact or Hidden), is decided in ArkSignal and only you can change it. Your upload address is a secret; if it ever leaks, make a new one on your station's page and the old one stops working at once.

## Tempest without Home Assistant

The [bridge](bridge/) is a small program (and a ready-made container, `ghcr.io/mallison01/arksignal-tempest-bridge`) that listens to your Tempest hub's local broadcast and sends the same readings. No Tempest cloud account is involved.

## Troubleshooting

* **Nothing shows up on ArkSignal.** The first reading is sent about 20 seconds after setup, then every minute. Check Home Assistant's log for *ArkSignal*; it reports once if sending fails and once when it works again.
* **A value is missing or wrong.** Open **Configure** and pick the right sensor for it, or clear it.
* **The upload address is refused.** Copy it again from **My Weather Stations**; it ends in `/wx/relay/` and a long secret.
* **"Could not reach ArkSignal" with an `http://` address.** Versions before 1.0.2 could not follow the redirect most sites make from `http://` to `https://`. Update to 1.0.2 or later, or change `http://` to `https://` in the address.

## For developers

* `python3 tests/test_mapping.py`: how sensors are recognised and the payload is built (plain Python).
* `tests/ha/`: a fake Tempest device, to run the integration inside a real Home Assistant container.
* `python3 bridge/test_bridge.py`: the Tempest bridge.
* HACS reads the version from the release tag, which must match `version` in `custom_components/arksignal/manifest.json`. Pushing a `v*` tag also builds the bridge container.

## License

MIT, see [LICENSE](LICENSE).
