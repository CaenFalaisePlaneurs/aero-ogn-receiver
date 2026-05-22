from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SCRIPT = PROJECT_ROOT / "scripts/install.sh"


class InstallScriptTests(unittest.TestCase):
    def test_install_script_is_valid_posix_sh(self):
        result = subprocess.run(
            ["sh", "-n", str(INSTALL_SCRIPT)],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_install_script_help_documents_curl_entrypoint(self):
        result = subprocess.run(
            ["sh", str(INSTALL_SCRIPT), "--help"],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("curl -fsSL", result.stdout)
        self.assertIn("raw.githubusercontent.com", result.stdout)
        self.assertIn("AERO_PI_OGN_RECEIVER_NAME", result.stdout)


if __name__ == "__main__":
    unittest.main()
