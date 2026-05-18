import unittest

from aero_pi_ogn_receiver.core.architecture import resolve_binary_arch


class ArchitectureTests(unittest.TestCase):
    def test_auto_selects_arm_on_64_bit_os_for_runtime_compatibility(self):
        self.assertEqual(resolve_binary_arch("auto", host_arch="arm64"), "arm")
        self.assertEqual(resolve_binary_arch("auto", host_arch="aarch64"), "arm")

    def test_auto_selects_arm_on_32_bit_os(self):
        self.assertEqual(resolve_binary_arch("auto", host_arch="armhf"), "arm")
        self.assertEqual(resolve_binary_arch("auto", host_arch="armel"), "arm")
        self.assertEqual(resolve_binary_arch("auto", host_arch="arm"), "arm")

    def test_explicit_arch_is_preserved(self):
        self.assertEqual(resolve_binary_arch("arm"), "arm")
        self.assertEqual(resolve_binary_arch("arm64"), "arm64")
        self.assertEqual(resolve_binary_arch("rpi_gpu"), "rpi_gpu")


if __name__ == "__main__":
    unittest.main()
