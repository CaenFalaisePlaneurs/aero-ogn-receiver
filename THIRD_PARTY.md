# Third-Party Runtime Components

This project is licensed under GPL-3.0-or-later. It installs and manages
official Open Glider Network receiver binaries as separate third-party runtime
components.

The official OGN binaries are not relicensed by this project. In particular,
`ogn-decode` is treated as a closed-source upstream binary and should be updated
only through the pinned and verified binary manifest.

The repository must not contain `ogn-rf`, `ogn-decode`, or any
`rtlsdr-ogn` binary archive. Those files are downloaded only during an explicit
install or update operation, then verified before extraction.

The committed manifest records:

- versioned upstream archive URLs,
- upstream MD5 values from `http://download.glidernet.org/md5.txt`,
- project-maintained SHA-256 values used for required verification,
- archive sizes and provenance metadata when known.

MD5 is retained as upstream metadata and a corruption reference. SHA-256 is the
required install-time verification check.

