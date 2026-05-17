import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from aero_ogn_receiver.setup import setup, uninstall


class SetupIntegrationTests(unittest.TestCase):
    def test_setup_writes_config_rendered_config_and_units_under_test_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            with redirect_stdout(StringIO()):
                result = setup.main(
                    [
                        "--root",
                        str(root),
                        "--skip-download",
                        "--no-daemon-reload",
                    ]
                )

            self.assertEqual(result, 0)
            self.assertTrue((root / "etc/aero-ogn-receiver/config.yaml").exists())
            rendered = root / "etc/aero-ogn-receiver/rtlsdr-ogn.conf"
            self.assertIn('Call = "LFAS";', rendered.read_text(encoding="utf-8"))
            rf_unit = root / "etc/systemd/system/aero-ogn-rf.service"
            decode_unit = root / "etc/systemd/system/aero-ogn-decode.service"
            self.assertTrue(rf_unit.exists())
            self.assertTrue(decode_unit.exists())
            self.assertIn("/usr/bin/procServ", rf_unit.read_text(encoding="utf-8"))
            self.assertIn("127.0.0.1:50000", rf_unit.read_text(encoding="utf-8"))
            self.assertIn("/usr/bin/procServ", decode_unit.read_text(encoding="utf-8"))
            self.assertIn("127.0.0.1:50001", decode_unit.read_text(encoding="utf-8"))
            self.assertTrue((root / "etc/systemd/system/aero-ogn-receiver.target").exists())

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
            self.assertFalse((root / "etc/systemd/system/aero-ogn-rf.service").exists())
            self.assertTrue((root / "etc/aero-ogn-receiver/config.yaml").exists())

    def test_uninstall_purge_removes_config_and_binaries_when_requested(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with redirect_stdout(StringIO()):
                setup_result = setup.main(
                    ["--root", str(root), "--skip-download", "--no-daemon-reload"]
                )
            self.assertEqual(setup_result, 0)
            opt_dir = root / "opt/aero-ogn-receiver"
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
            self.assertFalse((root / "etc/aero-ogn-receiver").exists())
            self.assertFalse(opt_dir.exists())


if __name__ == "__main__":
    unittest.main()
