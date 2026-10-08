import json, socket, threading, time, unittest
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
import arksignal_tempest_bridge as b

OBS = {"serial_number": "ST-00000512", "type": "obs_st", "hub_sn": "HB-00013030",
       "obs": [[1588948614, 0.18, 4.0, 7.5, 144, 3, 1000.0, 22.0, 50.26, 32800, 3.5, 410, 0.254, 1, 12.0, 2, 2.41, 1]], "firmware_revision": 129}


class T(unittest.TestCase):
    def test_observation_becomes_a_payload_with_units(self):
        s = b.State()
        self.assertTrue(s.feed(OBS))
        p = s.payload()
        self.assertEqual(p["temperature"], {"value": 22.0, "unit": "°C"})
        self.assertEqual(p["wind_speed"]["value"], 4.0)
        self.assertEqual(p["wind_gust"]["value"], 7.5)
        self.assertEqual(p["wind_direction"]["value"], 144.0)
        self.assertEqual(p["solar_radiation"]["value"], 410.0)
        self.assertEqual(p["uv_index"]["value"], 3.5)
        self.assertEqual(p["rain_today"]["value"], 0.25)
        self.assertEqual(p["rain_rate"]["value"], 15.24)          # 0.254 mm in 1 minute
        self.assertEqual(p["lightning_count"]["value"], 2)
        self.assertEqual(p["lightning_distance"], {"value": 12.0, "unit": "km"})
        self.assertEqual(p["pressure"]["value"], 1000.0)          # no elevation given: as the station reads it

    def test_sea_level_pressure(self):
        # 300 m above sea level, 15 C: about 3.6 % more than the station reads
        self.assertAlmostEqual(b.sea_level_hpa(980.0, 15.0, 300.0), 1015.8, delta=1.0)
        self.assertEqual(b.sea_level_hpa(980.0, 15.0, 0), 980.0)

    def test_rain_and_lightning_add_up_through_the_day_and_reset_at_midnight(self):
        today = [date(2026, 10, 8)]
        s = b.State(today=lambda: today[0])
        s.feed(OBS); s.feed(OBS)
        self.assertEqual(s.payload()["rain_today"]["value"], 0.51)
        self.assertEqual(s.payload()["lightning_count"]["value"], 4)
        today[0] = date(2026, 10, 9)
        s.feed(OBS)
        self.assertEqual(s.payload()["rain_today"]["value"], 0.25)
        self.assertEqual(s.payload()["lightning_count"]["value"], 2)

    def test_a_strike_event_updates_the_distance(self):
        s = b.State(); s.feed(OBS)
        s.feed({"type": "evt_strike", "evt": [1588948700, 27, 3848]})
        self.assertEqual(s.payload()["lightning_distance"]["value"], 27.0)

    def test_other_messages_and_junk_are_ignored(self):
        s = b.State()
        for m in ({"type": "rapid_wind", "ob": [1, 2, 3]}, {"type": "hub_status"}, {"type": "obs_st", "obs": [[1, 2]]}, [], "x", None):
            self.assertFalse(s.feed(m))
        self.assertIsNone(s.payload())

    def test_posting_and_the_whole_path_over_udp(self):
        got = []

        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                got.append((self.path, json.loads(self.rfile.read(int(self.headers["Content-Length"]))), self.headers["Content-Type"]))
                self.send_response(200); self.end_headers(); self.wfile.write(b"success")

            def log_message(self, *a): pass
        srv = HTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_port}/wx/relay/TOKEN"
        ok, text = b.post(url, {"x": 1})
        self.assertTrue(ok); self.assertEqual(text, "success"); self.assertEqual(got[0][0], "/wx/relay/TOKEN"); self.assertEqual(got[0][2], "application/json")
        # the real loop, fed by a UDP datagram like the hub's
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); probe.bind(("", 0)); port = probe.getsockname()[1]; probe.close()
        th = threading.Thread(target=b.run, args=(url, 0, 0, port, lambda m: None), daemon=True); th.start()
        time.sleep(0.5)
        tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for _ in range(20):
            tx.sendto(json.dumps(OBS).encode(), ("127.0.0.1", port)); time.sleep(0.3)
            if len(got) > 1: break
        self.assertGreater(len(got), 1)
        self.assertEqual(got[-1][1]["temperature"]["value"], 22.0)

    def test_a_refused_post_is_reported_not_raised(self):
        ok, text = b.post("http://127.0.0.1:9/wx/relay/T", {"x": 1}, timeout=2)
        self.assertFalse(ok); self.assertTrue(text)


if __name__ == "__main__":
    unittest.main()
