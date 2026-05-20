import unittest

from aero_pi_ogn_receiver.cli.status import (
    _find_rtl_sdr_usb_device,
    _runtime_stability_from_journal,
)


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

    def test_runtime_stability_fails_on_child_crash(self):
        check = _runtime_stability_from_journal(
            "\n".join(
                [
                    "procServ[1559]: Demodulator is 17sec behind !",
                    "procServ[1559]: @@@ Received a sigChild for process 1784. The process was killed by signal 11",
                    'procServ[1559]: @@@ Restarting child "./ogn-decode"',
                    "procServ[1558]: RF_Acq.Exec() ... Dropped a slot",
                ]
            )
        )

        self.assertEqual(check.state, "FAIL")
        self.assertIn("1 child crash(es)", check.evidence)
        self.assertIn("1 child restart(s)", check.evidence)
        self.assertIn("1 demod lag warning(s)", check.evidence)
        self.assertIn("1 RF dropped slot(s)", check.evidence)

    def test_runtime_stability_warns_on_demod_lag_without_crash(self):
        check = _runtime_stability_from_journal(
            "\n".join(
                [
                    "procServ[1559]: Demodulator is 12sec behind !",
                    "procServ[1558]: RF_Acq.Exec() ... Dropped a slot",
                ]
            )
        )

        self.assertEqual(check.state, "WARN")
        self.assertIn("1 demod lag warning(s)", check.evidence)
        self.assertIn("1 RF dropped slot(s)", check.evidence)

    def test_runtime_stability_ok_without_markers(self):
        check = _runtime_stability_from_journal("procServ[1559]: APRS -> # logresp")

        self.assertEqual(check.state, "OK")


if __name__ == "__main__":
    unittest.main()
