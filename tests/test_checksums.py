import hashlib
import tempfile
import unittest
from pathlib import Path

from aero_pi_ogn_receiver.core.checksums import (
    ChecksumMismatch,
    md5_file,
    sha256_file,
    verify_file_hash,
)


class ChecksumTests(unittest.TestCase):
    def test_hash_helpers_match_hashlib(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.bin"
            data = b"aero ogn receiver\n"
            path.write_bytes(data)

            self.assertEqual(sha256_file(path), hashlib.sha256(data).hexdigest())
            self.assertEqual(md5_file(path), hashlib.md5(data).hexdigest())

    def test_verify_file_hash_raises_on_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.bin"
            path.write_bytes(b"data")

            with self.assertRaises(ChecksumMismatch):
                verify_file_hash(path, "0" * 64, "sha256")


if __name__ == "__main__":
    unittest.main()

