import unittest
from unittest.mock import patch

from aero_ogn_receiver.cli import logs


class LogFilterTests(unittest.TestCase):
    def test_traffic_filter_keeps_useful_aprs_lines(self):
        self.assertTrue(logs.is_traffic_log_line("APRS <- LFAS>OGNSDR:/092407h4855.64N"))
        self.assertTrue(logs.is_traffic_log_line("APRS_Sender.Exec() ... Connected"))
        self.assertTrue(logs.is_traffic_log_line("APRS -> # logresp LFAS verified"))

    def test_traffic_filter_drops_default_heartbeat_noise(self):
        self.assertFalse(logs.is_traffic_log_line("APRS -> # aprsc 2.1.20 server banner"))
        self.assertFalse(logs.is_traffic_log_line("APRS time - system time = +0"))
        self.assertFalse(logs.is_traffic_log_line("HTTP_Server.Exec() ... Request for /status.html"))
        self.assertFalse(
            logs.is_traffic_log_line(
                "HTTP_Server.Exec() ... Request for /aircraft-list-short.txt"
            )
        )

    def test_traffic_filter_can_include_heartbeat_lines(self):
        self.assertTrue(
            logs.is_traffic_log_line(
                "APRS -> # aprsc 2.1.20 server banner",
                include_heartbeat=True,
            )
        )
        self.assertTrue(
            logs.is_traffic_log_line("APRS time - system time = +0", include_heartbeat=True)
        )

    def test_aircraft_snapshot_strips_empty_lines(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b"\nABC123 12km 1000m\n\nDEF456 22km 1200m\n"

        with patch("urllib.request.urlopen", return_value=Response()):
            snapshot = logs.fetch_aircraft_snapshot("http://example.test/aircraft")

        self.assertEqual(snapshot, "ABC123 12km 1000m\nDEF456 22km 1200m")


if __name__ == "__main__":
    unittest.main()
