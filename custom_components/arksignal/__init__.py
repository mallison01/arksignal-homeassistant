"""ArkSignal weather: sends a weather station's readings (any device in Home Assistant) to your private ArkSignal upload address once a minute."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_call_later, async_track_time_interval

from .const import CONF_INTERVAL, CONF_MAPPING, CONF_URL, CONF_WEATHER, DEFAULT_INTERVAL, DOMAIN, MIN_INTERVAL
from .mapping import build_payload

_LOGGER = logging.getLogger(__name__)


class Sender:
    """Reads the chosen sensors and posts them. Quiet when things work; says so once when sending starts failing and once when it recovers."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass, self.entry = hass, entry
        self.failing = False
        self.last_ok: datetime | None = None
        self._cancel = []

    def _state(self, entity_id):
        s = self.hass.states.get(entity_id)
        return None if s is None else (s.state, dict(s.attributes))

    async def send(self, _now=None) -> bool:
        opts = self.entry.options
        payload = build_payload(opts.get(CONF_MAPPING, {}), self._state, opts.get(CONF_WEATHER))
        if payload is None:
            return False
        payload["source"] = "home-assistant arksignal 1.0"
        try:
            async with async_get_clientsession(self.hass).post(self.entry.data[CONF_URL], json=payload, timeout=20) as resp:
                ok = resp.status < 300 or resp.status == 429   # 429: a moment too soon after the last one, not a problem
                if not ok:
                    raise RuntimeError(f"HTTP {resp.status}")
        except Exception as err:  # network down, address changed, station switched off
            if not self.failing:
                _LOGGER.warning("Could not send the weather to ArkSignal: %s", err)
            self.failing = True
            return False
        if self.failing:
            _LOGGER.info("Sending the weather to ArkSignal works again")
        self.failing, self.last_ok = False, datetime.now()
        return True

    def start(self) -> None:
        seconds = max(MIN_INTERVAL, int(self.entry.options.get(CONF_INTERVAL, DEFAULT_INTERVAL)))
        self._cancel.append(async_track_time_interval(self.hass, self.send, timedelta(seconds=seconds)))
        self._cancel.append(async_call_later(self.hass, 20, self.send))   # the first reading soon after start, once the sensors have values

    @callback
    def stop(self) -> None:
        for c in self._cancel:
            c()
        self._cancel.clear()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    sender = Sender(hass, entry)
    sender.start()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = sender
    entry.async_on_unload(sender.stop)
    entry.async_on_unload(entry.add_update_listener(_reload))
    return True


async def _reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return True
