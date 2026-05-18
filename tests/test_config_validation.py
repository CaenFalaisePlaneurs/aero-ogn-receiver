import unittest

from aero_pi_ogn_receiver.core import paths
from aero_pi_ogn_receiver.core.config_model import ConfigError, load_config, parse_config


class ConfigValidationTests(unittest.TestCase):
    def test_example_config_validates(self):
        config = load_config(paths.example_config_path())

        self.assertEqual(config.receiver.name, "LFAS")
        self.assertEqual(config.ogn.version, "0.3.2")
        self.assertEqual(config.ogn.binary_arch, "auto")
        self.assertFalse(config.radio.bias_tee)

    def test_invalid_coordinates_fail_validation(self):
        valid = load_config(paths.example_config_path())
        data = {
            "receiver": {
                "name": valid.receiver.name,
                "latitude": 91.0,
                "longitude": valid.receiver.longitude,
                "altitude_m": valid.receiver.altitude_m,
            },
            "radio": {
                "ppm_correction": valid.radio.ppm_correction,
                "gsm_calibration": valid.radio.gsm_calibration,
                "gsm_center_freq_mhz": valid.radio.gsm_center_freq_mhz,
                "gsm_gain_db": valid.radio.gsm_gain_db,
                "ogn_gain_db": valid.radio.ogn_gain_db,
                "bias_tee": valid.radio.bias_tee,
            },
            "ogn": {
                "aprs_server": valid.ogn.aprs_server,
                "version": valid.ogn.version,
                "binary_arch": valid.ogn.binary_arch,
            },
            "service": {"start_on_boot": valid.service.start_on_boot},
        }

        with self.assertRaises(ConfigError):
            parse_config(data)


if __name__ == "__main__":
    unittest.main()
