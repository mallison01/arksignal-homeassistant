#!/usr/bin/env python3
"""ArkSignal Tempest bridge.

A Tempest hub announces its readings on your own network (UDP broadcast, port 50222) without any internet service involved. This small program, run on any
computer on the same network (a Raspberry Pi, a NAS, a Docker host), listens to that broadcast and sends the readings to your private ArkSignal upload address.
Nothing is read from WeatherFlow's cloud and no account or token of theirs is used.

    python3 arksignal_tempest_bridge.py --url http://HOST/wx/relay/YOUR-TOKEN --elevation-ft 300

Settings can also come from the environment (ARKSIGNAL_URL, ARKSIGNAL_ELEVATION_FT or ARKSIGNAL_ELEVATION_M, ARKSIGNAL_INTERVAL, ARKSIGNAL_PORT).
Python 3.8 or newer, standard library only. The UDP message format is WeatherFlow's published Tempest UDP API (obs_st, evt_strike)."""
import argparse
import json
import math
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

VERSION = "1.0.0"
UDP_PORT = 50222


def sea_level_hpa(station_hpa, temp_c, elevation_m):
    """Tempest reports the pressure where it stands; weather maps use pressure reduced to sea level. Standard barometric reduction (the same one the NWS uses)."""
    if not elevation_m:
        return station_hpa
    return station_hpa * (1 - 0.0065 * elevation_m / (temp_c + 0.0065 * elevation_m + 273.15)) ** -5.257


class State:
    """The newest observation plus the running totals that a day needs (rain and lightning today, reset at local midnight)."""

    def __init__(self, elevation_m=0.0, today=None):
        self.elevation_m = elevation_m
        self.today = today or (lambda: datetime.now().date())
        self.day = self.today()
        self.rain_mm = 0.0
        self.strikes = 0
        self.last_strike_km = None
        self.obs = None
        self.obs_time = 0
        self.serial = ""

    def _roll(self):
        d = self.today()
        if d != self.day:
            self.day, self.rain_mm, self.strikes = d, 0.0, 0

    def feed(self, msg):
        """One UDP message (already decoded from JSON). Returns True when it changed what will be sent."""
        if not isinstance(msg, dict):
            return False
        self._roll()
        kind = msg.get("type")
        if kind == "obs_st" and msg.get("obs"):
            o = msg["obs"][-1]
            if len(o) < 18:
                return False
            self.obs, self.obs_time, self.serial = o, o[0], msg.get("serial_number", "")
            interval = o[17] or 1
            if o[12] is not None:
                self.rain_mm += float(o[12])
            if o[15]:
                self.strikes += int(o[15])
                if o[14]:
                    self.last_strike_km = float(o[14])
            self._rate = (float(o[12] or 0) / interval) * 60.0   # mm that fell in the report interval, as mm per hour
            return True
        if kind == "evt_strike" and msg.get("evt"):
            self.last_strike_km = float(msg["evt"][1])
            return True
        return False

    def payload(self):
        """The reading in the form ArkSignal's relay takes: every value carries its own unit."""
        if not self.obs:
            return None
        o = self.obs
        temp = float(o[7])
        out = {
            "temperature": {"value": round(temp, 1), "unit": "°C"},
            "humidity": {"value": round(float(o[8]), 1), "unit": "%"},
            "pressure": {"value": round(sea_level_hpa(float(o[6]), temp, self.elevation_m), 1), "unit": "hPa"},
            "wind_speed": {"value": round(float(o[2]), 2), "unit": "m/s"},
            "wind_gust": {"value": round(float(o[3]), 2), "unit": "m/s"},
            "wind_direction": {"value": float(o[4]), "unit": "°"},
            "rain_today": {"value": round(self.rain_mm, 2), "unit": "mm"},
            "rain_rate": {"value": round(getattr(self, "_rate", 0.0), 2), "unit": "mm/h"},
            "solar_radiation": {"value": float(o[11]), "unit": "W/m²"},
            "uv_index": {"value": float(o[10]), "unit": "UV index"},
            "lightning_count": {"value": self.strikes, "unit": ""},
        }
        if self.last_strike_km is not None:
            out["lightning_distance"] = {"value": self.last_strike_km, "unit": "km"}
        out["source"] = "arksignal-tempest-bridge " + VERSION
        return out


def post(url, payload, timeout=15):
    """Send one reading. Returns (ok, text). A 429 means 'a moment too soon', not a failure."""
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", "User-Agent": "arksignal-tempest-bridge/" + VERSION}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return True, r.read(200).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code == 429, f"HTTP {e.code}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def listen(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except OSError:
            pass
    s.bind(("", port))
    return s


def run(url, elevation_m, interval, port, log=print):
    st = State(elevation_m)
    sock = listen(port)
    sock.settimeout(5)
    last_sent, sent_obs = 0.0, 0
    log(f"Listening for the Tempest hub on UDP port {port}; sending to {url.split('/wx/')[0]}/wx/relay/... every {interval} s.")
    if not elevation_m:
        log("No elevation given: the pressure is sent as the station reads it. Add --elevation-ft or --elevation-m for sea-level pressure.")
    while True:
        try:
            data, _addr = sock.recvfrom(4096)
            st.feed(json.loads(data.decode("utf-8", "replace")))
        except socket.timeout:
            pass
        except ValueError:
            continue
        now = time.time()
        if st.obs and now - last_sent >= interval and st.obs_time != sent_obs:
            ok, text = post(url, st.payload())
            if ok:
                sent_obs = st.obs_time
            log(("Sent " if ok else "Could not send: ") + f"{st.serial or 'Tempest'} {text}")
            last_sent = now


def main(argv=None):
    p = argparse.ArgumentParser(description="Send your Tempest hub's local readings to ArkSignal.")
    p.add_argument("--url", default=os.environ.get("ARKSIGNAL_URL", ""), help="your private upload address from My Weather Stations (http://host/wx/relay/TOKEN)")
    p.add_argument("--elevation-ft", type=float, default=None, help="height of the station above sea level, in feet (for sea-level pressure)")
    p.add_argument("--elevation-m", type=float, default=None, help="the same, in meters")
    p.add_argument("--interval", type=int, default=int(os.environ.get("ARKSIGNAL_INTERVAL", "60")), help="seconds between sends (default 60)")
    p.add_argument("--port", type=int, default=int(os.environ.get("ARKSIGNAL_PORT", str(UDP_PORT))), help="UDP port of the hub's broadcast (default 50222)")
    a = p.parse_args(argv)
    if not a.url.startswith(("http://", "https://")) or "/wx/relay/" not in a.url:
        sys.exit("Give the upload address from My Weather Stations, which looks like http://host/wx/relay/TOKEN (--url or ARKSIGNAL_URL).")
    elev = a.elevation_m
    if elev is None:
        ft = a.elevation_ft if a.elevation_ft is not None else float(os.environ.get("ARKSIGNAL_ELEVATION_FT", "0") or 0)
        elev = float(os.environ.get("ARKSIGNAL_ELEVATION_M", "0") or 0) or ft * 0.3048
    run(a.url, elev, max(30, a.interval), a.port)


if __name__ == "__main__":
    main()
