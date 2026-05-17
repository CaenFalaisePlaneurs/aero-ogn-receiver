from __future__ import annotations

import argparse
import sys

from aero_ogn_receiver.core.manifest import ManifestError, load_manifest


def add_binaries_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("binaries", help="Inspect pinned OGN binary manifest")
    binary_subparsers = parser.add_subparsers(dest="binaries_command", required=True)

    list_parser = binary_subparsers.add_parser("list", help="List committed OGN binaries")
    list_parser.set_defaults(handler=list_command)


def list_command(args: argparse.Namespace) -> int:
    try:
        manifest = load_manifest()
    except ManifestError as exc:
        print(f"FAIL manifest: {exc}", file=sys.stderr)
        return 1

    for entry in manifest.iter_entries():
        print(f"{entry.version} {entry.arch}")
        print(f"  URL:          {entry.url}")
        print(f"  SHA-256:      {entry.sha256}")
        print(f"  MD5:          {entry.md5}")
        print(f"  Size:         {entry.size_bytes} bytes")
        print(f"  Last-Modified:{entry.upstream_last_modified}")
        print(f"  Archive root: {entry.archive_root}")
    return 0

