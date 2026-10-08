"""Which of a device's sensors is which weather value, and the payload ArkSignal's relay takes. No Home Assistant imports: this is plain Python so it can be tested on its own.

Every value is sent with the unit Home Assistant shows for it ({"temperature": {"value": 21.5, "unit": "°C"}}); ArkSignal converts, so nothing is converted here."""
import math

# key, label (the keys are the ones ArkSignal's relay understands)
METRICS = [
    ("temperature", "Temperature"), ("humidity", "Humidity"), ("pressure", "Pressure (sea level)"), ("wind_speed", "Wind speed"), ("wind_gust", "Wind gust"),
    ("wind_direction", "Wind direction"), ("rain_today", "Rain today"), ("rain_rate", "Rain rate"), ("solar_radiation", "Solar radiation"), ("uv_index", "UV index"),
    ("dew_point", "Dew point"), ("lightning_count", "Lightning strikes today"), ("lightning_distance", "Lightning distance"),
]

# device classes, words that name it, words that rule an entity out, words that make it a better choice, and the units it may carry
RULES = {
    "temperature": dict(dc=("temperature",), words=("temperature", "temp"), bad=("dew", "feels", "feel", "wet", "heat", "chill", "apparent", "soil", "water", "indoor", "inside", "battery", "probe", "cpu", "hub", "min", "max", "forecast"),
                        good=("outdoor", "outside", "air", "ambient"), units=("°c", "°f", "k")),
    "dew_point": dict(dc=(), words=("dew",), bad=("indoor", "inside"), good=(), units=("°c", "°f", "k")),
    "humidity": dict(dc=("humidity",), words=("humidity",), bad=("indoor", "inside", "soil", "leaf", "absolute"), good=("outdoor", "outside", "relative"), units=("%",)),
    "pressure": dict(dc=("pressure", "atmospheric_pressure"), words=("pressure", "barometric", "barometer"), bad=("station", "absolute", "abs", "vapor", "vapour"), good=("sea", "relative", "barometric", "rel"),
                     units=("hpa", "mbar", "mb", "inhg", "kpa", "mmhg", "psi", "pa")),
    "wind_speed": dict(dc=("wind_speed",), words=("wind speed", "wind_speed", "windspeed", "average wind", "wind avg", "wind_avg", "wind"), bad=("gust", "lull", "max", "bearing", "direction", "dir", "chill", "peak", "daily"), good=("speed", "avg", "average"),
                       units=("km/h", "m/s", "mph", "kn", "ft/s")),
    "wind_gust": dict(dc=(), words=("gust",), bad=("max daily", "daily", "peak", "direction", "bearing"), good=("wind",), units=("km/h", "m/s", "mph", "kn", "ft/s")),
    "wind_direction": dict(dc=(), words=("direction", "bearing", "wind_dir", "winddir", "wind dir"), bad=("gust", "lull", "max", "daily"), good=("wind",), units=("°",)),
    "rain_today": dict(dc=("precipitation",), words=("today", "daily", "day", "rain", "precipitation"), bad=("rate", "intensity", "week", "month", "year", "yesterday", "hourly", "hour", "event", "last", "total", "probability", "forecast"),
                       good=("today", "daily", "day"), units=("mm", "in", "cm")),
    "rain_rate": dict(dc=("precipitation_intensity",), words=("rate", "intensity"), bad=("forecast", "probability"), good=("rain", "precip"), units=("mm/h", "in/h", "mm/hr", "in/hr")),
    "solar_radiation": dict(dc=("irradiance",), words=("solar", "radiation", "irradiance"), bad=("lux", "illuminance", "max", "daily", "energy"), good=("solar",), units=("w/m²", "w/m2")),
    "uv_index": dict(dc=(), words=("uv",), bad=("uva", "uvb", "max", "daily", "forecast", "alert"), good=("index",), units=("uv index", "uvi", "")),
    "lightning_count": dict(dc=(), words=("lightning count", "strike count", "lightning_num", "strikes", "lightning strike", "lightning_strike_count", "lightning"), bad=("distance", "time", "last", "energy"), good=("count", "today", "daily", "number"), units=("", "strikes", "count")),
    "lightning_distance": dict(dc=("distance",), words=("lightning distance", "strike distance", "lightning_dist", "lightning", "strike"), bad=("count", "num"), good=("distance", "dist"), units=("km", "mi", "m", "ft")),
}
# an entity must name the thing, not just have the right device class, for these (many unrelated sensors share a class)
NAME_REQUIRED = {"dew_point", "wind_direction", "wind_gust", "uv_index", "lightning_count", "lightning_distance", "rain_rate", "rain_today", "solar_radiation", "wind_speed"}


def _text(info):
    return " ".join(str(info.get(k) or "") for k in ("entity_id", "name", "original_name", "translation_key")).lower().replace("_", " ")


def _score(metric, info):
    r = RULES[metric]
    text = _text(info)
    dc = (info.get("device_class") or "").lower()
    unit = (info.get("unit") or "").lower()
    named = any(w.replace("_", " ") in text for w in r["words"])
    dc_ok = dc in r["dc"]
    if metric in NAME_REQUIRED and not named:
        return 0
    if not (named or dc_ok):
        return 0
    if r["units"] and unit not in r["units"]:
        return 0
    if any(b in text for b in r["bad"]):
        return 0
    return 1 + 3 * dc_ok + 2 * named + 2 * sum(1 for g in r["good"] if g in text)


def suggest(entities):
    """entities: [{entity_id, name, original_name, translation_key, device_class, unit}] of one device -> {metric: entity_id}. Each entity is used for at most one value."""
    taken, out = set(), {}
    scored = []
    for metric, _label in METRICS:
        for e in entities:
            s = _score(metric, e)
            if s:
                scored.append((s, -len(e["entity_id"]), metric, e["entity_id"]))
    for s, _l, metric, eid in sorted(scored, reverse=True):
        if metric not in out and eid not in taken:
            out[metric] = eid
            taken.add(eid)
    return out


# the attributes a Home Assistant `weather` entity offers instead of separate sensors: metric -> (attribute, attribute holding its unit)
WEATHER_ATTRS = {"temperature": ("temperature", "temperature_unit"), "dew_point": ("dew_point", "temperature_unit"), "humidity": ("humidity", None), "pressure": ("pressure", "pressure_unit"),
                 "wind_speed": ("wind_speed", "wind_speed_unit"), "wind_gust": ("wind_gust_speed", "wind_speed_unit"), "wind_direction": ("wind_bearing", None), "uv_index": ("uv_index", None)}
DEFAULT_UNITS = {"temperature": "°C", "dew_point": "°C", "humidity": "%", "pressure": "hPa", "wind_speed": "km/h", "wind_gust": "km/h", "wind_direction": "°", "uv_index": "UV index"}


def _number(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def build_payload(mapping, get_state, weather_entity=None):
    """mapping {metric: entity_id}; get_state(entity_id) -> (state text, attributes dict) or None. Returns the JSON object to send, or None when nothing has a value.
    A `weather` entity fills in whatever the sensors do not give."""
    out = {}
    for metric, _label in METRICS:
        eid = mapping.get(metric)
        st = get_state(eid) if eid else None
        if not st:
            continue
        val = _number(st[0])
        if val is None:
            continue
        out[metric] = {"value": val, "unit": str((st[1] or {}).get("unit_of_measurement") or "")}
    if weather_entity:
        w = get_state(weather_entity)
        if w:
            attrs = w[1] or {}
            for metric, (attr, unit_attr) in WEATHER_ATTRS.items():
                if metric in out:
                    continue
                val = _number(attrs.get(attr))
                if val is not None:
                    out[metric] = {"value": val, "unit": str(attrs.get(unit_attr) or DEFAULT_UNITS[metric]) if unit_attr else DEFAULT_UNITS[metric]}
    return out or None
