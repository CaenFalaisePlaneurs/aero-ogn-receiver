import unittest

from aero_ogn_receiver.core import paths
from aero_ogn_receiver.core.config_model import load_config, parse_config
from aero_ogn_receiver.core.render import render_ogn_config


class RenderTests(unittest.TestCase):
    def test_render_output_contains_core_ogn_settings(self):
        config = load_config(paths.example_config_path())
        rendered = render_ogn_config(config)

        self.assertIn('Call = "LFAS";', rendered)
        self.assertIn("Latitude = 48.92746;", rendered)
        self.assertIn("Longitude = -0.14842;", rendered)
        self.assertIn("Altitude = 157;", rendered)
        self.assertIn("FreqCorr = 0;", rendered)
        self.assertIn("Gain = 50;", rendered)
        self.assertIn('Server = "aprs.glidernet.org:14580";', rendered)
        self.assertNotIn("GSM:", rendered)

    def test_render_output_can_include_gsm_calibration(self):
        config = load_config(paths.example_config_path())
        data = {
            "receiver": {
                "name": config.receiver.name,
                "latitude": config.receiver.latitude,
                "longitude": config.receiver.longitude,
                "altitude_m": config.receiver.altitude_m,
            },
            "radio": {
                "ppm_correction": config.radio.ppm_correction,
                "gsm_calibration": True,
                "gsm_center_freq_mhz": 950,
                "gsm_gain_db": 25,
                "ogn_gain_db": config.radio.ogn_gain_db,
                "bias_tee": config.radio.bias_tee,
            },
            "ogn": {
                "aprs_server": config.ogn.aprs_server,
                "version": config.ogn.version,
                "binary_arch": config.ogn.binary_arch,
            },
            "service": {"start_on_boot": config.service.start_on_boot},
        }

        rendered = render_ogn_config(parse_config(data))

        self.assertIn("GSM:", rendered)
        self.assertIn("CenterFreq = 950;", rendered)
        self.assertIn("Gain = 25;", rendered)


if __name__ == "__main__":
    unittest.main()
