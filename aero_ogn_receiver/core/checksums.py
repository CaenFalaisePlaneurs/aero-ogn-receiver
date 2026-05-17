from __future__ import annotations

import hashlib
from pathlib import Path


class ChecksumMismatch(ValueError):
    """Raised when a file digest does not match the expected value."""


def file_hash(path: Path, algorithm: str, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    return file_hash(path, "sha256")


def md5_file(path: Path) -> str:
    return file_hash(path, "md5")


def verify_file_hash(path: Path, expected_hex: str, algorithm: str) -> str:
    actual = file_hash(path, algorithm)
    if actual.lower() != expected_hex.lower():
        raise ChecksumMismatch(
            f"{path} {algorithm} mismatch: expected {expected_hex}, got {actual}"
        )
    return actual

