# ArkSignal Tempest bridge

Sends your Tempest station's readings to your private ArkSignal upload address, using only what the Tempest hub announces on **your own network** (WeatherFlow's local UDP broadcast). No Tempest cloud account, token or internet service is involved.

1. On ArkSignal open **My Weather Stations**, add a station and choose *Home Assistant, a Tempest bridge or a script*. Copy its upload address (it ends in `/wx/relay/` and a long secret).
2. On any always-on computer on the same network as the Tempest hub:

   ```
   python3 arksignal_tempest_bridge.py --url http://HOST/wx/relay/YOUR-TOKEN --elevation-ft 300
   ```
   or use Docker: `docker run -d --restart unless-stopped --network host -e ARKSIGNAL_URL=http://HOST/wx/relay/YOUR-TOKEN -e ARKSIGNAL_ELEVATION_FT=300 ghcr.io/mallison01/arksignal-tempest-bridge:latest` (host networking is required so the hub's broadcast is heard; the image runs on PCs and Raspberry Pis; see also `compose.example.yaml`).
3. Within a minute or two the station shows readings on its page. Leave it running.

Notes: the elevation is only for the pressure (the Tempest reports the pressure where it stands, weather maps use sea-level pressure); rain and lightning *today* are added up by the bridge and reset at local midnight; it sends one reading a minute. Home Assistant users can use the ArkSignal integration instead (it also handles Tempest through Home Assistant's own WeatherFlow integration).

Python 3.8+, standard library only. Run `python3 test_bridge.py` for the tests.
