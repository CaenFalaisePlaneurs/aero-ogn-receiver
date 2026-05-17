# Security Policy

`aero-ogn-receiver` is a manager for official OGN receiver binaries. The Python
source, templates, installer scaffolding, and documentation are GPL-3.0-or-later.
The downloaded OGN binaries remain third-party runtime components.

## Binary Trust Boundary

`ogn-decode` is treated as a closed-source upstream binary. The project does not
audit or relicense it, and it does not commit it to Git.

## Download And Update Policy

- No boot-time downloads.
- No automatic OGN binary updates.
- No use of mutable `latest` URLs in the committed manifest.
- Downloads occur only during explicit install or update operations.
- Downloaded archives must match the committed SHA-256 before extraction.
- Upstream MD5 values are stored as metadata, but are not the primary security
  check.

## Future Improvements

The next supply-chain improvement should be signed project manifests or signed
project releases so users can verify both the binary metadata and the source
release that contains it.

