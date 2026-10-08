from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo

# name, device class, unit, value
SENSORS = [
    ("Air temperature", "temperature", "°C", 21.5), ("Dew point", "temperature", "°C", 12.0), ("Feels like", "temperature", "°C", 22.0),
    ("Humidity", "humidity", "%", 55), ("Sea level pressure", "pressure", "hPa", 1013.2), ("Station pressure", "pressure", "hPa", 990.0),
    ("Wind speed", "wind_speed", "m/s", 4.5), ("Wind gust", "wind_speed", "m/s", 8.0), ("Wind lull", "wind_speed", "m/s", 1.0), ("Wind direction", None, "°", 225),
    ("Precipitation rate", "precipitation_intensity", "mm/h", 0.0), ("Precipitation today", "precipitation", "mm", 5.08), ("Precipitation yesterday", "precipitation", "mm", 1.0),
    ("Solar radiation", "irradiance", "W/m²", 410), ("Illuminance", "illuminance", "lx", 45000), ("UV index", None, "UV index", 3.5),
    ("Lightning count", None, None, 2), ("Lightning distance", "distance", "km", 12), ("Battery", "battery", "%", 90),
]


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([Fake(entry, *s) for s in SENSORS])


class Fake(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, entry, name, dc, unit, value):
        self._attr_name, self._attr_device_class, self._attr_native_unit_of_measurement, self._attr_native_value = name, dc, unit, value
        self._attr_unique_id = f"{entry.entry_id}-{name}"
        self._attr_device_info = DeviceInfo(identifiers={("fakestation", entry.entry_id)}, name="Fake Tempest", manufacturer="Test")
