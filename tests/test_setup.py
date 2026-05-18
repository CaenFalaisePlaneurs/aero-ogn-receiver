import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from aero_pi_ogn_receiver.setup import setup, uninstall


class SetupIntegrationTests(unittest.TestCase):
    def test_setup_writes_config_rendered_config_and_units_under_test_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            with redirect_stdout(StringIO()):
                result = setup.main(
                    [
                        "--root",
                        str(root),
                        "--venv-dir",
                        str(root / "home/pi/aero-pi-ogn-receiver-venv"),
                        "--skip-download",
                        "--no-daemon-reload",
                    ]
                )

            self.assertEqual(result, 0)
            self.assertTrue((root / "etc/aero-pi-ogn-receiver/config.yaml").exists())
            self.assertTrue((root / "var/lib/aero-pi-ogn-receiver/install-state.json").exists())
            rendered = root / "etc/aero-pi-ogn-receiver/rtlsdr-ogn.conf"
            self.assertIn('Call = "LFAS";', rendered.read_text(encoding="utf-8"))
            rf_unit = root / "etc/systemd/system/aero-pi-ogn-rf.service"
            decode_unit = root / "etc/systemd/system/aero-pi-ogn-decode.service"
            self.assertTrue(rf_unit.exists())
            self.assertTrue(decode_unit.exists())
            self.assertIn("/usr/bin/procServ", rf_unit.read_text(encoding="utf-8"))
            self.assertIn("127.0.0.1:50000", rf_unit.read_text(encoding="utf-8"))
            self.assertIn("/usr/bin/procServ", decode_unit.read_text(encoding="utf-8"))
            self.assertIn("127.0.0.1:50001", decode_unit.read_text(encoding="utf-8"))
            self.assertTrue((root / "etc/systemd/system/aero-pi-ogn-receiver.target").exists())
            readme = root / "home/pi/aero-pi-ogn-receiver-venv/README-aero-pi-ogn-receiver.md"
            self.assertTrue(readme.exists())
            readme_text = readme.read_text(encoding="utf-8")
            self.assertIn("status --live", readme_text)
            self.assertIn("aircraft --watch 5", readme_text)
            self.assertIn("aircraft --raw", readme_text)
            self.assertIn("logs traffic --follow", readme_text)
            self.assertIn(
                "https://caenfalaiseplaneurs.github.io/aero-pi-ogn-receiver/quickstart/",
                readme_text,
            )
            self.assertIn("aero-pi-ogn-uninstall --complete", readme_text)
            self.assertIn(
                "https://caenfalaiseplaneurs.github.io/aero-pi-ogn-receiver/",
                readme_text,
            )

    def test_uninstall_removes_units_and_preserves_config_by_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with redirect_stdout(StringIO()):
                setup_result = setup.main(
                    ["--root", str(root), "--skip-download", "--no-daemon-reload"]
                )
            self.assertEqual(setup_result, 0)

            with redirect_stdout(StringIO()):
                result = uninstall.main(["--root", str(root), "--no-daemon-reload"])

            self.assertEqual(result, 0)
            self.assertFalse((root / "etc/systemd/system/aero-pi-ogn-rf.service").exists())
            self.assertTrue((root / "etc/aero-pi-ogn-receiver/config.yaml").exists())
            self.assertFalse((root / "etc/aero-pi-ogn-receiver/rtlsdr-ogn.conf").exists())
            self.assertFalse((root / "var/lib/aero-pi-ogn-receiver").exists())
            self.assertFalse((root / "var/log/aero-pi-ogn-receiver").exists())

    def test_uninstall_purge_removes_config_and_binaries_when_requested(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with redirect_stdout(StringIO()):
                setup_result = setup.main(
                    ["--root", str(root), "--skip-download", "--no-daemon-reload"]
                )
            self.assertEqual(setup_result, 0)
            opt_dir = root / "opt/aero-pi-ogn-receiver"
            self.assertTrue(opt_dir.exists())

            with redirect_stdout(StringIO()):
                result = uninstall.main(
                    [
                        "--root",
                        str(root),
                        "--purge",
                        "--remove-binaries",
                        "--no-daemon-reload",
                    ]
                )

            self.assertEqual(result, 0)
            self.assertFalse((root / "etc/aero-pi-ogn-receiver").exists())
            self.assertFalse(opt_dir.exists())

    def test_complete_uninstall_preserves_config_and_removes_project_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with redirect_stdout(StringIO()):
                setup_result = setup.main(
                    ["--root", str(root), "--skip-download", "--no-daemon-reload"]
                )
            self.assertEqual(setup_result, 0)

            with redirect_stdout(StringIO()):
                result = uninstall.main(["--root", str(root), "--complete"])

            self.assertEqual(result, 0)
            self.assertTrue((root / "etc/aero-pi-ogn-receiver/config.yaml").exists())
            self.assertFalse((root / "etc/aero-pi-ogn-receiver/rtlsdr-ogn.conf").exists())
            self.assertFalse((root / "etc/systemd/system/aero-pi-ogn-rf.service").exists())
            self.assertFalse((root / "opt/aero-pi-ogn-receiver").exists())
            self.assertFalse((root / "var/lib/aero-pi-ogn-receiver").exists())
            self.assertFalse((root / "var/log/aero-pi-ogn-receiver").exists())


if __name__ == "__main__":
    unittest.main()
