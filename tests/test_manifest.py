import unittest

from aero_ogn_receiver.core.manifest import ManifestError, load_manifest, parse_manifest


class ManifestTests(unittest.TestCase):
    def test_manifest_parses_committed_entries(self):
        manifest = load_manifest()

        arm = manifest.get("0.3.2", "arm")
        arm64 = manifest.get("0.3.2", "arm64")
        rpi_gpu = manifest.get("0.3.2", "rpi_gpu")

        self.assertEqual(arm.archive_root, "rtlsdr-ogn-0.3.2")
        self.assertEqual(arm.md5, "33a1f70c74538660274fa653e9ba6503")
        self.assertEqual(len(arm.sha256), 64)
        self.assertIn("rtlsdr-ogn-bin-ARM-0.3.2.tgz", arm.url)
        self.assertEqual(arm64.md5, "ac659a05f45a27b59667758aac26b073")
        self.assertEqual(arm64.sha256, "400a53849c440cfdce533297637200385077c7c576ccb98ab8d0eed8d9c54319")
        self.assertIn("rtlsdr-ogn-bin-arm64-0.3.2.tgz", arm64.url)
        self.assertEqual(rpi_gpu.size_bytes, 395567)

    def test_manifest_rejects_latest_urls(self):
        with self.assertRaises(ManifestError):
            parse_manifest(
                {
                    "ogn_binaries": {
                        "0.3.2": {
                            "arm": {
                                "url": "http://download.glidernet.org/arm/latest.tgz",
                                "sha256": "0" * 64,
                                "md5": "0" * 32,
                                "size_bytes": 1,
                                "upstream_last_modified": "2024-03-19T22:24:55Z",
                                "archive_root": "rtlsdr-ogn-0.3.2",
                            }
                        }
                    }
                }
            )


if __name__ == "__main__":
    unittest.main()
