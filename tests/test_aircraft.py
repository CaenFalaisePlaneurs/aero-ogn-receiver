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

    def test_parse_ogn_receiver_short_summary_and_detail_pairs(self):
        tracks = aircraft.parse_aircraft_lines(
            [
                "FLRDD8DED [   38/  131sec] 1:2:DD8DED F*  <30.1m/s> < 7.9dB>, "
                "<0.8bit/packet>, < -1.99(0.15)kHz> -10.2dB@10km(118) "
                "DD8DED/05/7.4.3",
                "120926: [ +48.92981,  -0.12933]deg   619m  -1.4m/s  "
                "25.1m/s 251.5deg -10.0deg/s __2 04x06m O :01f__ -1.79kHz  "
                "4.2/15.5dB/2  0e     1.4km 079.7deg +17.8deg +  !   *",
                "FLRDD8F34 [   20/  194sec] 1:2:DD8F34 F*  <20.0m/s> < 5.3dB>, "
                "<2.4bit/packet>, < +2.58(0.07)kHz> -11.2dB@10km(35)",
                "120850: [ +48.94136,  -0.13945]deg   840m  -0.6m/s  "
                "26.2m/s 349.5deg  +6.7deg/s __2 03x05m O :00f__ +2.60kHz  "
                "3.0/12.5dB/2  2e     1.7km 023.0deg +22.1deg +  !   *",
            ]
        )

        self.assertEqual(len(tracks), 2)
        self.assertEqual(tracks[0].identifier, "FLRDD8DED")
        self.assertEqual(tracks[0].age, "131s")
        self.assertEqual(tracks[0].latitude, "+48.92981")
        self.assertEqual(tracks[0].longitude, "-0.12933")
        self.assertEqual(tracks[0].altitude_m, "619")
        self.assertEqual(tracks[0].speed_kt, "49")
        self.assertEqual(tracks[0].heading_deg, "251.5")
        self.assertEqual(tracks[0].quality, "4.2/15.5dB/2 -1.79kHz")
        self.assertEqual(tracks[1].identifier, "FLRDD8F34")
        self.assertEqual(tracks[1].speed_kt, "51")
        self.assertEqual(tracks[1].quality, "3.0/12.5dB/2 +2.60kHz")

    def test_parse_ogn_receiver_summary_line_keeps_fallback_quality(self):
        track = aircraft.parse_aircraft_line(
            "FLRDD8DED [   38/  131sec] 1:2:DD8DED F*  <30.1m/s> < 7.9dB>, "
            "<0.8bit/packet>, < -1.99(0.15)kHz> -10.2dB@10km(118)"
        )

        self.assertEqual(track.identifier, "FLRDD8DED")
        self.assertEqual(track.age, "131s")
        self.assertEqual(track.quality, "7.9dB -1.99kHz")

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
