# Testing inside a real Home Assistant

`fakestation/` is a test-only integration: one device ("Fake Tempest") with sensors named the way real integrations name theirs.

1. Copy `custom_components/arksignal` and `tests/ha/fakestation` into `<config>/custom_components/` of a Home Assistant container (for example `docker run -d --name hatest --network host -v <config>:/config ghcr.io/home-assistant/home-assistant:stable`; put `default_config:` in `configuration.yaml`).
2. In the ArkSignal portal repo run `python weather_ha_test.py` from `tests/` (it onboards the container, adds the fake device, runs the ArkSignal setup flow through Home Assistant's REST API, checks the sensors were found by themselves, checks the readings arrive on a portal station converted, and checks the options flow and the log).
