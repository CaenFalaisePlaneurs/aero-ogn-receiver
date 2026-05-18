import unittest
from unittest.mock import patch

from aero_pi_ogn_receiver.cli import aircraft


class AircraftTests(unittest.TestCase):
    def test_parse_local_decoder_track_line(self):
        track = aircraft.parse_aircraft_line(
            "1.234s 01:ABCDEF [+48.92746, -000.14842]deg 157m, "
            "090deg 055kt #02 12.3/4.5dB +1.2kHz"
        )

        self.assertEqual(track.identifier, "01:ABCDEF")
        self.assertEqual(track.latitude, "+48.92746")
        self.assertEqual(track.longitude, "-000.14842")
        self.assertEqual(track.altitude_m, "157")
        self.assertEqual(track.speed_kt, "055")
        self.assertEqual(track.heading_deg, "090")
        self.assertEqual(track.quality, "12.3/4.5dB +1.2kHz")

    def test_parse_aprs_position_track_line(self):
        track = aircraft.parse_aircraft_line(
            "FLRDDE1A3>OGFLR,qAS,LFAS:/074716h4726.50N/00922.64E'"
            "086/015/A=003848 id0ADDE1A3 +020fpm +0.0rot 14.5dB 0e +0.5kHz"
        )

        self.assertEqual(track.identifier, "FLRDDE1A3")
        self.assertEqual(track.latitude, "47.44167")
        self.assertEqual(track.longitude, "9.37733")
        self.assertEqual(track.altitude_m, "1173")
        self.assertEqual(track.speed_kt, "15")
        self.assertEqual(track.heading_deg, "86")
        self.assertEqual(track.quality, "14.5dB +0.5kHz")

    def test_aprs_name_uses_ddb_name_when_present(self):
        track = aircraft.parse_aircraft_line(
            "FLRABCDEF>OGFLR,qAS,LFAS:/074716h4726.50N/00922.64E'"
            "086/015/A=003848 Name=\"F-CABC\" 12.0dB"
        )

        self.assertEqual(track.identifier, "F-CABC")

    def test_fetch_aircraft_text(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b"line 1\n"

        with patch("urllib.request.urlopen", return_value=Response()):
            text = aircraft.fetch_aircraft_text("http://example.test/aircraft")

        self.assertEqual(text, "line 1\n")


if __name__ == "__main__":
    unittest.main()
