from __future__ import annotations

import argparse
import sys
from pathlib import Path

from aero_ogn_receiver.core import paths
from aero_ogn_receiver.core.config_model import ConfigError, load_config
from aero_ogn_receiver.core.render import render_ogn_config


def add_config_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("config", help="Validate and render receiver config")
    config_subparsers = parser.add_subparsers(dest="config_command", required=True)

    validate = config_subparsers.add_parser("validate", help="Validate YAML config")
    validate.add_argument("--config", type=Path, help="Config file to validate")
    validate.set_defaults(handler=validate_command)

    render = config_subparsers.add_parser("render", help="Render native OGN config")
    render.add_argument("--config", type=Path, help="Config file to render")
    render.add_argument("--output", type=Path, help="Write rendered config to this path")
    render.set_defaults(handler=render_command)


def validate_command(args: argparse.Namespace) -> int:
    candidates = [args.config] if args.config else _default_validate_paths()
    exit_code = 0
    for path in candidates:
        try:
            load_config(path)
        except (ConfigError, FileNotFoundError) as exc:
            print(f"FAIL {path}: {exc}", file=sys.stderr)
            exit_code = 1
        else:
            print(f"OK   {path}")
    return exit_code


def render_command(args: argparse.Namespace) -> int:
    config_path = args.config or paths.default_read_config_path()
    try:
        config = load_config(config_path)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"FAIL {config_path}: {exc}", file=sys.stderr)
        return 1

    rendered = render_ogn_config(config)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote {args.output}")
        return 0

    print(rendered, end="" if rendered.endswith("\n") else "\n")
    return 0


def _default_validate_paths() -> list[Path]:
    candidates = [paths.example_config_path()]
    if paths.CONFIG_PATH.exists() and paths.CONFIG_PATH not in candidates:
        candidates.append(paths.CONFIG_PATH)
    return candidates

