import unittest

from aero_ogn_receiver.cli.status import _find_rtl_sdr_usb_device


class StatusTests(unittest.TestCase):
    def test_find_rtl_sdr_usb_device_by_usb_id(self):
        output = "\n".join(
            [
                "Bus 001 Device 004: ID 045e:0750 Microsoft Corp. Wired Keyboard 600",
                "Bus 001 Device 005: ID 0bda:2838 Realtek Semiconductor Corp. RTL2838 DVB-T",
            ]
        )

        self.assertEqual(
            _find_rtl_sdr_usb_device(output),
            "Bus 001 Device 005: ID 0bda:2838 Realtek Semiconductor Corp. RTL2838 DVB-T",
        )

    def test_find_rtl_sdr_usb_device_returns_none_when_missing(self):
        self.assertIsNone(
            _find_rtl_sdr_usb_device(
                "Bus 001 Device 004: ID 045e:0750 Microsoft Corp. Wired Keyboard 600"
            )
        )


if __name__ == "__main__":
    unittest.main()

