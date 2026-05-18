import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO

from aero_pi_ogn_receiver.cli.main import main
from aero_pi_ogn_receiver.core import paths


class CliTests(unittest.TestCase):
    def test_module_help_runs(self):
        completed = subprocess.run(
            [sys.executable, "-m", "aero_pi_ogn_receiver", "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0)
        self.assertIn("aero-pi-ogn", completed.stdout)

    def test_required_commands_provide_help(self):
        commands = [
            ["config", "--help"],
            ["config", "validate", "--help"],
            ["config", "render", "--help"],
            ["binaries", "list", "--help"],
            ["status", "--help"],
            ["aircraft", "--help"],
            ["logs", "--help"],
            ["logs", "traffic", "--help"],
            ["service", "status", "--help"],
            ["healthcheck", "--help"],
        ]
        for command in commands:
            with self.subTest(command=command):
                completed = subprocess.run(
                    [sys.executable, "-m", "aero_pi_ogn_receiver", *command],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(completed.returncode, 0)
                self.assertIn("usage:", completed.stdout)

    def test_config_validate_command_accepts_example(self):
        with redirect_stdout(StringIO()):
            result = main(["config", "validate", "--config", str(paths.example_config_path())])
        self.assertEqual(result, 0)

    def test_config_render_command_accepts_example(self):
        with redirect_stdout(StringIO()):
            result = main(["config", "render", "--config", str(paths.example_config_path())])
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
