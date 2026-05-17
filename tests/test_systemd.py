import unittest

from aero_ogn_receiver.core import systemd


class SystemdCommandTests(unittest.TestCase):
    def test_journalctl_command_for_all_logs(self):
        command = systemd.journalctl_command("all", follow=True, lines=50)

        self.assertEqual(command[:4], ["journalctl", "-u", "aero-ogn-rf.service", "-u"])
        self.assertIn("aero-ogn-decode.service", command)
        self.assertIn("-f", command)
        self.assertIn("50", command)

    def test_systemctl_status_command_for_rf(self):
        command = systemd.systemctl_command("status", "rf")

        self.assertEqual(command, ["systemctl", "status", "aero-ogn-rf.service"])


if __name__ == "__main__":
    unittest.main()
