---
layout: default
title: OGN Binaries
permalink: /binaries/
---

# OGN Binaries And Third-Party Runtime Components

This project is a manager/wrapper around official OGN receiver binaries. It does
not reimplement `ogn-rf` or `ogn-decode`, and it does not relicense those
binaries.

The repository must contain only source code, templates, documentation, tests,
and a binary manifest. The installer will download official OGN archives from
`download.glidernet.org` only during explicit install/update operations, verify
them against the committed SHA-256 manifest, and install them under
`/opt/aero-pi-ogn-receiver/ogn`.

`binary_arch: "auto"` currently selects the 32-bit ARM OGN archive on Raspberry
Pi OS, including 64-bit Raspberry Pi OS, because OGN 0.3.2 arm64 crashed during
decoder connection testing on the Pi target. Explicit `arm`, `arm64`, and
`rpi_gpu` values are also accepted for manual testing.

Do not commit `ogn-rf`, `ogn-decode`, or any `rtlsdr-ogn` archive.

## Third-Party Runtime Components

This project is licensed under GPL-3.0-or-later. It installs and manages
official Open Glider Network receiver binaries as separate third-party runtime
components.

The official OGN binaries are not relicensed by this project. In particular,
`ogn-decode` is treated as a closed-source upstream binary and should be updated
only through the pinned and verified binary manifest.

The repository must not contain `ogn-rf`, `ogn-decode`, or any `rtlsdr-ogn`
binary archive. Those files are downloaded only during an explicit install or
update operation, then verified before extraction.

The committed manifest records:

- versioned upstream archive URLs,
- upstream MD5 values from `http://download.glidernet.org/md5.txt`,
- project-maintained SHA-256 values used for required verification,
- archive sizes and provenance metadata when known.

MD5 is retained as upstream metadata and a corruption reference. SHA-256 is the
required install-time verification check.

## License

Project source code, installer code, templates, and documentation are licensed
under GPL-3.0-or-later.

Official OGN binaries are separate third-party runtime components and are not
relicensed by this project. See the [security policy](security.md) for the
binary trust boundary and download/update rules.
