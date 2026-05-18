from __future__ import annotations

import argparse
import os
import shlex
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path


README_FILENAME = "README-aero-pi-ogn-receiver.md"
DEFAULT_REPO_URL = "https://github.com/CaenFalaisePlaneurs/aero-pi-ogn-receiver.git"
DOCS_URL = "https://caenfalaiseplaneurs.github.io/aero-pi-ogn-receiver/"
QUICKSTART_URL = "https://caenfalaiseplaneurs.github.io/aero-pi-ogn-receiver/quickstart/"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m aero_pi_ogn_receiver.setup.venv_readme",
        description="Write the aero-pi-ogn-receiver command README into a virtual environment.",
    )
    parser.add_argument(
        "venv_dir",
        nargs="?",
        type=Path,
        help="Virtual environment directory. Defaults to the current Python virtual environment.",
    )
    parser.add_argument(
        "--repo-url",
        default=DEFAULT_REPO_URL,
        help="Git repository URL used in upgrade commands",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    venv_dir = args.venv_dir or detect_venv_dir()
    if venv_dir is None:
        print("Error: cannot detect a Python virtual environment", file=sys.stderr)
        return 1
    path = write_venv_readme(venv_dir, repo_url=args.repo_url)
    print(path)
    return 0


def detect_venv_dir() -> Path | None:
    prefix = Path(sys.prefix)
    if (prefix / "pyvenv.cfg").exists():
        return prefix

    executable_venv = Path(sys.executable).resolve().parent.parent
    if (executable_venv / "pyvenv.cfg").exists():
        return executable_venv

    if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        return prefix
    return None


def write_venv_readme(venv_dir: Path, repo_url: str = DEFAULT_REPO_URL) -> Path:
    venv_dir = venv_dir.expanduser().resolve()
    venv_dir.mkdir(parents=True, exist_ok=True)
    readme_path = venv_dir / README_FILENAME
    readme_path.write_text(render_venv_readme(venv_dir, repo_url=repo_url), encoding="utf-8")
    readme_path.chmod(0o644)
    _match_venv_owner(readme_path, venv_dir)
    return readme_path


def render_venv_readme(venv_dir: Path, repo_url: str = DEFAULT_REPO_URL) -> str:
    venv_dir = venv_dir.expanduser().resolve()
    bin_dir = venv_dir / "bin"
    aero_pi_ogn = bin_dir / "aero-pi-ogn"
    python = bin_dir / "python"
    uninstall = bin_dir / "aero-pi-ogn-uninstall"

    return f"""# aero-pi-ogn-receiver Command Sheet

This file is generated for this virtual environment:

```bash
{_q(venv_dir)}
```

Use these commands for common receiver tasks. For configuration details,
troubleshooting, binary architecture notes, and less common maintenance tasks,
read the full project documentation:

{DOCS_URL}

For the minimal plane-checking workflow:

{QUICKSTART_URL}

## Check Status

```bash
source {_q(venv_dir / "bin" / "activate")}
{_q(aero_pi_ogn)} status --live
{_q(aero_pi_ogn)} aircraft --watch 5
{_q(aero_pi_ogn)} aircraft --raw
{_q(aero_pi_ogn)} service status
{_q(aero_pi_ogn)} logs --lines 100
{_q(aero_pi_ogn)} logs traffic --follow
```

## Start, Stop, Restart

```bash
sudo systemctl start aero-pi-ogn-receiver.target
sudo systemctl stop aero-pi-ogn-receiver.target
sudo systemctl restart aero-pi-ogn-receiver.target
sudo systemctl status aero-pi-ogn-rf.service aero-pi-ogn-decode.service --no-pager
```

## Edit And Validate Config

```bash
sudo nano /etc/aero-pi-ogn-receiver/config.yaml
{_q(aero_pi_ogn)} config validate --config /etc/aero-pi-ogn-receiver/config.yaml
sudo {_q(aero_pi_ogn)} config render --config /etc/aero-pi-ogn-receiver/config.yaml --output /etc/aero-pi-ogn-receiver/rtlsdr-ogn.conf
sudo systemctl restart aero-pi-ogn-receiver.target
```

## Upgrade

```bash
{_q(python)} -m pip install --upgrade --force-reinstall git+{repo_url}
sudo {_q(python)} -m aero_pi_ogn_receiver.setup.setup
sudo systemctl restart aero-pi-ogn-receiver.target
{_q(aero_pi_ogn)} status --live
```

## Uninstall

Preserve `/etc/aero-pi-ogn-receiver/config.yaml` and remove the receiver
integration, binaries, recorded system packages, state, and logs:

```bash
sudo {_q(uninstall)} --complete
rm -rf {_q(venv_dir)}
```

To also remove `/etc/aero-pi-ogn-receiver/config.yaml`, add `--purge` to the
uninstall command.
"""


def _match_venv_owner(readme_path: Path, venv_dir: Path) -> None:
    if not hasattr(os, "geteuid") or os.geteuid() != 0:
        return
    try:
        stat_result = venv_dir.stat()
        shutil.chown(readme_path, user=stat_result.st_uid, group=stat_result.st_gid)
    except (LookupError, OSError):
        return


def _q(path: Path) -> str:
    return shlex.quote(str(path))


if __name__ == "__main__":
    raise SystemExit(main())
