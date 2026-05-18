---
layout: default
title: Development
permalink: /development/
---

# Development

Run the test suite from the repository root:

```bash
python3 -m unittest discover -s tests -v
```

Useful local smoke checks:

```bash
python3 -m aero_pi_ogn_receiver config validate
python3 -m aero_pi_ogn_receiver binaries list
python3 -m aero_pi_ogn_receiver status --live
python3 -m aero_pi_ogn_receiver.setup.setup --dry-run
```
