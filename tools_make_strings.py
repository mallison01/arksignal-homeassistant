"""Writes strings.json and translations/en.json from one place (run it after changing a label)."""
import json, os
here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_components", "arksignal")
labels = {"temperature": "Temperature", "humidity": "Humidity", "pressure": "Pressure (sea level)", "wind_speed": "Wind speed", "wind_gust": "Wind gust", "wind_direction": "Wind direction",
          "rain_today": "Rain today", "rain_rate": "Rain rate", "solar_radiation": "Solar radiation", "uv_index": "UV index", "dew_point": "Dew point",
          "lightning_count": "Lightning strikes today", "lightning_distance": "Lightning distance", "weather": "Weather entity (fills in anything missing)"}
sens = "These were found automatically from the device you chose. Check each one and change or clear it. Leave a value empty if your station does not measure it. Units are sent as Home Assistant shows them; ArkSignal converts."
strings = {
    "config": {
        "step": {
            "user": {"title": "ArkSignal weather", "description": "On ArkSignal open My Weather Stations, add a station and choose Home Assistant. Paste its upload address here (it ends in /wx/relay/ and a long secret).",
                     "data": {"url": "Upload address"}},
            "device": {"title": "Choose the weather station", "description": "Pick the device in Home Assistant that is your weather station (a Tempest, Ecowitt, Ambient, Davis or similar). Leave it empty to choose the sensors one by one.",
                       "data": {"device": "Device"}},
            "sensors": {"title": "Check the sensors", "description": sens, "data": labels},
        },
        "error": {
            "bad_address": "That does not look like an ArkSignal upload address. It should look like http://host/wx/relay/ followed by a long secret.",
            "unknown_address": "ArkSignal does not know that address. Copy it again from My Weather Stations.",
            "cannot_connect": "Could not reach ArkSignal. Check the address and that Home Assistant can reach the internet.",
            "nothing_chosen": "Choose at least one sensor or a weather entity.",
        },
        "abort": {"already_configured": "That ArkSignal station is already set up."},
    },
    "options": {"step": {"init": {"title": "ArkSignal weather", "description": "Change which sensors are sent, or how often.", "data": dict(labels, interval="Send every (seconds)")}}},
}
for rel in ("strings.json", os.path.join("translations", "en.json")):
    os.makedirs(os.path.dirname(os.path.join(here, rel)), exist_ok=True)
    with open(os.path.join(here, rel), "w", encoding="utf-8", newline="\n") as f:
        json.dump(strings, f, indent=2, ensure_ascii=False)
        f.write("\n")
print("written")
