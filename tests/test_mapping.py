import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "custom_components", "arksignal"))
import mapping as m


def E(eid, name, dc=None, unit=None, tk=None):
    return {"entity_id": eid, "name": name, "original_name": name, "device_class": dc, "unit": unit, "translation_key": tk}


# what Home Assistant's WeatherFlow (Tempest) integration offers, as its entity names go
TEMPEST = [E("sensor.st_00012345_air_temperature", "Air temperature", "temperature", "°C"), E("sensor.st_00012345_dew_point", "Dew point", "temperature", "°C"),
           E("sensor.st_00012345_feels_like", "Feels like", "temperature", "°C"), E("sensor.st_00012345_wet_bulb_temperature", "Wet bulb temperature", "temperature", "°C"),
           E("sensor.st_00012345_humidity", "Humidity", "humidity", "%"), E("sensor.st_00012345_sea_level_pressure", "Sea level pressure", "pressure", "hPa"),
           E("sensor.st_00012345_barometric_pressure", "Barometric pressure", "pressure", "hPa"), E("sensor.st_00012345_station_pressure", "Station pressure", "pressure", "hPa"),
           E("sensor.st_00012345_wind_speed", "Wind speed", "wind_speed", "m/s"), E("sensor.st_00012345_wind_gust", "Wind gust", "wind_speed", "m/s"), E("sensor.st_00012345_wind_lull", "Wind lull", "wind_speed", "m/s"),
           E("sensor.st_00012345_wind_direction", "Wind direction", None, "°"), E("sensor.st_00012345_precipitation_rate", "Precipitation rate", "precipitation_intensity", "mm/h"),
           E("sensor.st_00012345_precipitation_today", "Precipitation today", "precipitation", "mm"), E("sensor.st_00012345_precipitation_yesterday", "Precipitation yesterday", "precipitation", "mm"),
           E("sensor.st_00012345_solar_radiation", "Solar radiation", "irradiance", "W/m²"), E("sensor.st_00012345_illuminance", "Illuminance", "illuminance", "lx"),
           E("sensor.st_00012345_uv_index", "UV index", None, "UV index"), E("sensor.st_00012345_lightning_count", "Lightning count", None, ""),
           E("sensor.st_00012345_lightning_distance", "Lightning distance", "distance", "km"), E("sensor.st_00012345_battery", "Battery", "battery", "%"), E("sensor.st_00012345_signal", "Signal strength", "signal_strength", "dBm")]
ECOWITT = [E("sensor.gw2000a_outdoor_temperature", "Outdoor temperature", "temperature", "°F"), E("sensor.gw2000a_indoor_temperature", "Indoor temperature", "temperature", "°F"),
           E("sensor.gw2000a_outdoor_humidity", "Outdoor humidity", "humidity", "%"), E("sensor.gw2000a_indoor_humidity", "Indoor humidity", "humidity", "%"),
           E("sensor.gw2000a_relative_pressure", "Relative pressure", "pressure", "inHg"), E("sensor.gw2000a_absolute_pressure", "Absolute pressure", "pressure", "inHg"),
           E("sensor.gw2000a_wind_speed", "Wind speed", "wind_speed", "mph"), E("sensor.gw2000a_wind_gust", "Wind gust", "wind_speed", "mph"), E("sensor.gw2000a_max_daily_gust", "Max daily gust", "wind_speed", "mph"),
           E("sensor.gw2000a_wind_direction", "Wind direction", None, "°"), E("sensor.gw2000a_rain_rate", "Rain rate", "precipitation_intensity", "in/h"),
           E("sensor.gw2000a_daily_rain", "Daily rain", "precipitation", "in"), E("sensor.gw2000a_weekly_rain", "Weekly rain", "precipitation", "in"), E("sensor.gw2000a_monthly_rain", "Monthly rain", "precipitation", "in"),
           E("sensor.gw2000a_solar_radiation", "Solar radiation", "irradiance", "W/m²"), E("sensor.gw2000a_uv_index", "UV index", None, "UV index"), E("sensor.gw2000a_dewpoint", "Dewpoint", "temperature", "°F"),
           E("sensor.gw2000a_lightning_strike_count", "Lightning strike count", None, ""), E("sensor.gw2000a_lightning_distance", "Lightning distance", "distance", "mi")]


class T(unittest.TestCase):
    def test_tempest(self):
        s = m.suggest(TEMPEST)
        self.assertEqual(s["temperature"], "sensor.st_00012345_air_temperature")
        self.assertEqual(s["dew_point"], "sensor.st_00012345_dew_point")
        self.assertEqual(s["humidity"], "sensor.st_00012345_humidity")
        self.assertEqual(s["pressure"], "sensor.st_00012345_sea_level_pressure")
        self.assertEqual(s["wind_speed"], "sensor.st_00012345_wind_speed")
        self.assertEqual(s["wind_gust"], "sensor.st_00012345_wind_gust")
        self.assertEqual(s["wind_direction"], "sensor.st_00012345_wind_direction")
        self.assertEqual(s["rain_rate"], "sensor.st_00012345_precipitation_rate")
        self.assertEqual(s["rain_today"], "sensor.st_00012345_precipitation_today")
        self.assertEqual(s["solar_radiation"], "sensor.st_00012345_solar_radiation")
        self.assertEqual(s["uv_index"], "sensor.st_00012345_uv_index")
        self.assertEqual(s["lightning_count"], "sensor.st_00012345_lightning_count")
        self.assertEqual(s["lightning_distance"], "sensor.st_00012345_lightning_distance")

    def test_ecowitt_prefers_outdoor_and_the_right_rain(self):
        s = m.suggest(ECOWITT)
        self.assertEqual(s["temperature"], "sensor.gw2000a_outdoor_temperature")
        self.assertEqual(s["humidity"], "sensor.gw2000a_outdoor_humidity")
        self.assertEqual(s["pressure"], "sensor.gw2000a_relative_pressure")
        self.assertEqual(s["wind_gust"], "sensor.gw2000a_wind_gust")
        self.assertEqual(s["rain_today"], "sensor.gw2000a_daily_rain")
        self.assertEqual(s["rain_rate"], "sensor.gw2000a_rain_rate")
        self.assertEqual(s["dew_point"], "sensor.gw2000a_dewpoint")
        self.assertEqual(s["lightning_count"], "sensor.gw2000a_lightning_strike_count")

    def test_each_sensor_is_used_once_and_nothing_unrelated_is_picked(self):
        s = m.suggest(TEMPEST)
        self.assertEqual(len(set(s.values())), len(s))
        self.assertNotIn("sensor.st_00012345_battery", s.values())
        self.assertNotIn("sensor.st_00012345_illuminance", s.values())
        self.assertEqual(m.suggest([E("sensor.cpu_temp", "CPU temperature", "temperature", "°C"), E("sensor.living_room", "Living room", "humidity", "%")]).get("temperature"), None)

    def test_payload_carries_each_value_with_its_unit_and_skips_the_unavailable(self):
        states = {"sensor.t": ("21.5", {"unit_of_measurement": "°C"}), "sensor.h": ("unavailable", {"unit_of_measurement": "%"}), "sensor.p": ("1013.2", {"unit_of_measurement": "hPa"})}
        p = m.build_payload({"temperature": "sensor.t", "humidity": "sensor.h", "pressure": "sensor.p", "wind_speed": "sensor.missing"}, states.get)
        self.assertEqual(p, {"temperature": {"value": 21.5, "unit": "°C"}, "pressure": {"value": 1013.2, "unit": "hPa"}})
        self.assertIsNone(m.build_payload({"humidity": "sensor.h"}, states.get))
        self.assertIsNone(m.build_payload({}, states.get))

    def test_a_weather_entity_fills_what_the_sensors_do_not_give(self):
        states = {"sensor.t": ("20", {"unit_of_measurement": "°C"}),
                  "weather.home": ("sunny", {"temperature": 99, "humidity": 40, "pressure": 29.9, "pressure_unit": "inHg", "wind_speed": 12, "wind_speed_unit": "mph", "wind_bearing": 270, "temperature_unit": "°F"})}
        p = m.build_payload({"temperature": "sensor.t"}, states.get, "weather.home")
        self.assertEqual(p["temperature"], {"value": 20.0, "unit": "°C"})          # the sensor wins
        self.assertEqual(p["humidity"], {"value": 40.0, "unit": "%"})
        self.assertEqual(p["pressure"], {"value": 29.9, "unit": "inHg"})
        self.assertEqual(p["wind_speed"], {"value": 12.0, "unit": "mph"})
        self.assertEqual(p["wind_direction"], {"value": 270.0, "unit": "°"})


if __name__ == "__main__":
    unittest.main()
