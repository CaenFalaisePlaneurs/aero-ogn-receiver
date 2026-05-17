from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from aero_ogn_receiver.core import paths, simple_yaml


class ManifestError(ValueError):
    """Raised when the binary manifest is invalid."""


_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_MD5_RE = re.compile(r"^[0-9a-fA-F]{32}$")


@dataclass(frozen=True)
class BinaryEntry:
    version: str
    arch: str
    url: str
    sha256: str
    md5: str
    size_bytes: int
    upstream_last_modified: str
    archive_root: str


@dataclass(frozen=True)
class BinaryManifest:
    entries: dict[str, dict[str, BinaryEntry]]

    def versions(self) -> list[str]:
        return sorted(self.entries)

    def architectures(self, version: str) -> list[str]:
        try:
            return sorted(self.entries[version])
        except KeyError as exc:
            raise ManifestError(f"unknown OGN binary version: {version}") from exc

    def get(self, version: str, arch: str) -> BinaryEntry:
        try:
            return self.entries[version][arch]
        except KeyError as exc:
            raise ManifestError(f"unknown OGN binary entry: {version} {arch}") from exc

    def iter_entries(self) -> Iterator[BinaryEntry]:
        for version in self.versions():
            for arch in self.architectures(version):
                yield self.entries[version][arch]


def load_manifest(path: Path | None = None) -> BinaryManifest:
    manifest_path = path or paths.manifest_path()
    data = simple_yaml.load(manifest_path)
    return parse_manifest(data)


def parse_manifest(data: object) -> BinaryManifest:
    if not isinstance(data, dict):
        raise ManifestError("manifest root must be a mapping")
    raw_versions = data.get("ogn_binaries")
    if not isinstance(raw_versions, dict) or not raw_versions:
        raise ManifestError("manifest must contain ogn_binaries")

    entries: dict[str, dict[str, BinaryEntry]] = {}
    for version, raw_arches in raw_versions.items():
        if not isinstance(version, str) or not version:
            raise ManifestError("manifest versions must be non-empty strings")
        if not isinstance(raw_arches, dict) or not raw_arches:
            raise ManifestError(f"version {version} must contain architectures")
        entries[version] = {}
        for arch, raw_entry in raw_arches.items():
            if not isinstance(arch, str) or not arch:
                raise ManifestError(f"version {version} contains an invalid architecture")
            if not isinstance(raw_entry, dict):
                raise ManifestError(f"{version} {arch} entry must be a mapping")
            entry = _parse_entry(version, arch, raw_entry)
            entries[version][arch] = entry

    return BinaryManifest(entries)


def _parse_entry(version: str, arch: str, raw: dict[str, object]) -> BinaryEntry:
    url = _required_str(raw, "url", version, arch)
    sha256 = _required_str(raw, "sha256", version, arch)
    md5 = _required_str(raw, "md5", version, arch)
    upstream_last_modified = _required_str(raw, "upstream_last_modified", version, arch)
    archive_root = _required_str(raw, "archive_root", version, arch)
    size_bytes = raw.get("size_bytes")

    if "latest" in url:
        raise ManifestError(f"{version} {arch} URL must be versioned, not latest")
    if not url.startswith(("http://", "https://")):
        raise ManifestError(f"{version} {arch} URL must be HTTP(S)")
    if not _SHA256_RE.match(sha256):
        raise ManifestError(f"{version} {arch} sha256 must be 64 hex characters")
    if not _MD5_RE.match(md5):
        raise ManifestError(f"{version} {arch} md5 must be 32 hex characters")
    if not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes <= 0:
        raise ManifestError(f"{version} {arch} size_bytes must be a positive integer")
    if not archive_root:
        raise ManifestError(f"{version} {arch} archive_root is required")

    return BinaryEntry(
        version=version,
        arch=arch,
        url=url,
        sha256=sha256.lower(),
        md5=md5.lower(),
        size_bytes=size_bytes,
        upstream_last_modified=upstream_last_modified,
        archive_root=archive_root,
    )


def _required_str(raw: dict[str, object], key: str, version: str, arch: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ManifestError(f"{version} {arch} {key} must be a non-empty string")
    return value

