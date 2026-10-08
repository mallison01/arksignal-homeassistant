"""Setting up: paste the upload address from ArkSignal, pick the weather station's device, check what was found. Options reopen the sensor step."""
from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr, entity_registry as er, selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_DEVICE, CONF_INTERVAL, CONF_MAPPING, CONF_URL, CONF_WEATHER, DEFAULT_INTERVAL, DOMAIN, MIN_INTERVAL
from .mapping import METRICS, suggest

ADDRESS_RE = re.compile(r"^https?://[^/\s]+/wx/relay/([A-Za-z0-9_-]{20,64})/?$")


async def _check(hass, url: str) -> str | None:
    """None when the address is a working ArkSignal upload address; otherwise the error key. An empty post to a good address is answered 'no usable readings' (400);
    an address that does not exist is answered 404."""
    try:
        async with async_get_clientsession(hass).post(url, json={}, timeout=15) as resp:
            if resp.status in (200, 400, 429):
                return None
            if resp.status == 404:
                return "unknown_address"
            return "cannot_connect"
    except Exception:
        return "cannot_connect"


def _device_entities(hass, device_id: str) -> list[dict[str, Any]]:
    reg = er.async_get(hass)
    out = []
    for ent in er.async_entries_for_device(reg, device_id):
        if ent.domain != "sensor" or ent.disabled_by:
            continue
        state = hass.states.get(ent.entity_id)
        out.append({"entity_id": ent.entity_id, "name": ent.name or ent.original_name or "", "original_name": ent.original_name or "", "translation_key": ent.translation_key or "",
                    "device_class": ent.device_class or ent.original_device_class or (state.attributes.get("device_class") if state else None),
                    "unit": (state.attributes.get("unit_of_measurement") if state else None) or ent.unit_of_measurement or ""})
    return out


def _sensors_schema(defaults: dict[str, Any], weather: str | None) -> vol.Schema:
    fields: dict[Any, Any] = {}
    for key, _label in METRICS:
        fields[vol.Optional(key, description={"suggested_value": defaults.get(key)})] = selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))
    fields[vol.Optional(CONF_WEATHER, description={"suggested_value": weather})] = selector.EntitySelector(selector.EntitySelectorConfig(domain="weather"))
    return vol.Schema(fields)


class ArkSignalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._url = ""
        self._defaults: dict[str, Any] = {}
        self._title = "ArkSignal weather"

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL].strip()
            m = ADDRESS_RE.match(url)
            if not m:
                errors[CONF_URL] = "bad_address"
            else:
                await self.async_set_unique_id(m.group(1))
                self._abort_if_unique_id_configured()
                err = await _check(self.hass, url)
                if err:
                    errors[CONF_URL] = err
                else:
                    self._url = url.rstrip("/")
                    return await self.async_step_device()
        return self.async_show_form(step_id="user", data_schema=vol.Schema({vol.Required(CONF_URL): str}), errors=errors)

    async def async_step_device(self, user_input=None):
        if user_input is not None:
            dev = user_input.get(CONF_DEVICE)
            if dev:
                self._defaults = suggest(_device_entities(self.hass, dev))
                d = dr.async_get(self.hass).async_get(dev)
                if d:
                    self._title = f"ArkSignal weather ({d.name_by_user or d.name})"
            return await self.async_step_sensors()
        return self.async_show_form(step_id="device", data_schema=vol.Schema({vol.Optional(CONF_DEVICE): selector.DeviceSelector()}))

    async def async_step_sensors(self, user_input=None):
        if user_input is not None:
            mapping = {k: v for k, v in user_input.items() if k in dict(METRICS) and v}
            weather = user_input.get(CONF_WEATHER)
            if not mapping and not weather:
                return self.async_show_form(step_id="sensors", data_schema=_sensors_schema(self._defaults, None), errors={"base": "nothing_chosen"})
            return self.async_create_entry(title=self._title, data={CONF_URL: self._url}, options={CONF_MAPPING: mapping, CONF_WEATHER: weather, CONF_INTERVAL: DEFAULT_INTERVAL})
        return self.async_show_form(step_id="sensors", data_schema=_sensors_schema(self._defaults, None))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ArkSignalOptionsFlow()


class ArkSignalOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        opts = self.config_entry.options
        if user_input is not None:
            mapping = {k: v for k, v in user_input.items() if k in dict(METRICS) and v}
            return self.async_create_entry(data={CONF_MAPPING: mapping, CONF_WEATHER: user_input.get(CONF_WEATHER), CONF_INTERVAL: int(user_input.get(CONF_INTERVAL, DEFAULT_INTERVAL))})
        schema = _sensors_schema(opts.get(CONF_MAPPING, {}), opts.get(CONF_WEATHER)).extend(
            {vol.Optional(CONF_INTERVAL, default=opts.get(CONF_INTERVAL, DEFAULT_INTERVAL)): selector.NumberSelector(selector.NumberSelectorConfig(min=MIN_INTERVAL, max=600, step=10, unit_of_measurement="s"))})
        return self.async_show_form(step_id="init", data_schema=schema)
