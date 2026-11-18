#!/usr/bin/env python3
"""Initialize, validate, repair, or summarize image-story wizard project state."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


STAGES = (
    "START",
    "BRIEF",
    "BENCHMARKS",
    "WRITING_PACK",
    "SCRIPT",
    "VOICE",
    "STORYBOARD",
    "VISUAL_STYLE",
    "CHARACTER_ANCHORS",
    "IMAGE_PROMPTS",
    "IMAGE_GENERATION",
    "ASSET_QC",
    "MUSIC",
    "PREVIEW",
    "FINAL_RENDER",
    "FEEDBACK",
)

STATUSES = ("未开始", "进行中", "待确认", "已确认", "需要返工", "已跳过")

HOSTS = ("dsh", "opencode", "codex", "workbuddy", "other")

CAPABILITY_KEYS = (
    "local_files",
    "attachments",
    "shell",
    "model_routing",
    "logged_in_browser",
    "tts",
    "image_generation",
    "hyperframes",
    "render",
)

HOST_LOCAL_FILES = {"dsh": True, "opencode": True, "codex": True, "workbuddy": False, "other": False}

PROJECT_DIRS = (
    "writing-pack",
    "audio",
    "characters",
    "images/references",
    "images/generated",
    "review",
    "renders",
)

REQUIRED_KEYS = (
    "schema_version",
    "project_id",
    "title",
    "project_root",
    "host",
    "current_stage",
    "stage_status",
    "pending_request",
    "next_stage",
    "decisions",
    "artifacts",
    "stage_history",
    "created_at",
    "updated_at",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"state file does not exist: {path}") from None
    except IsADirectoryError:
        raise ValueError(f"state path is a directory: {path}") from None
    except OSError as exc:
        raise ValueError(f"cannot read state file: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON at line {exc.lineno}, column {exc.colno}") from exc


def _is_timestamp(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate_state(data: dict, path: Path | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["state root must be an object"]

    for key in REQUIRED_KEYS:
        if key not in data:
            errors.append(f"missing required key: {key}")

    version = data.get("schema_version")
    if isinstance(version, bool) or not isinstance(version, int) or version != 1:
        errors.append("schema_version must be the integer 1")

    if data.get("current_stage") not in STAGES:
        errors.append(f"unknown current_stage: {data.get('current_stage')!r}")
    if data.get("stage_status") not in STATUSES:
        errors.append(f"unknown stage_status: {data.get('stage_status')!r}")

    next_stage = data.get("next_stage")
    if next_stage is not None and next_stage not in STAGES:
        errors.append(f"unknown next_stage: {next_stage!r}")

    for key in ("decisions", "artifacts"):
        if key in data and not isinstance(data[key], dict):
            errors.append(f"{key} must be an object")
    if "stage_history" in data:
        if not isinstance(data["stage_history"], list):
            errors.append("stage_history must be an array")
        elif any(not isinstance(entry, dict) for entry in data["stage_history"]):
            errors.append("every stage_history entry must be an object")

    for key in ("created_at", "updated_at"):
        if key in data and not _is_timestamp(data[key]):
            errors.append(f"{key} must be an ISO-8601 timestamp")

    title = data.get("title")
    if "title" in data and (not isinstance(title, str) or not title.strip()):
        errors.append("title must be a non-empty string")

    host = data.get("host")
    if not isinstance(host, dict):
        errors.append("host must be an object")
    else:
        if host.get("name") not in HOSTS:
            errors.append(f"host.name must be one of {', '.join(HOSTS)}")
        capabilities = host.get("capabilities")
        if not isinstance(capabilities, dict):
            errors.append("host.capabilities must be an object")
        else:
            missing = [key for key in CAPABILITY_KEYS if key not in capabilities]
            if missing:
                errors.append(f"host.capabilities missing keys: {', '.join(missing)}")
            unknown = [key for key in capabilities if key not in CAPABILITY_KEYS]
            if unknown:
                errors.append(f"host.capabilities has unknown keys: {', '.join(unknown)}")
            if any(not isinstance(value, bool) for value in capabilities.values()):
                errors.append("all host capability values must be booleans")

    root_value = data.get("project_root")
    if isinstance(root_value, str):
        root = Path(root_value)
        if not root.is_absolute():
            errors.append("project_root must be absolute")
        elif path is not None:
            try:
                matches = root.resolve() == path.parent.resolve()
            except OSError as exc:
                errors.append(f"cannot resolve project_root: {exc}")
                matches = True
            if not matches:
                errors.append(
                    "project_root does not match the state file directory; "
                    "run the repair command to move the root"
                )
    else:
        errors.append("project_root must be a string")

    return errors


def command_init(args: argparse.Namespace) -> int:
    root = Path(args.project_root).expanduser().resolve()
    state_path = root / "PROJECT_STATE.json"
    if state_path.exists():
        print(f"Refusing to overwrite existing state: {state_path}", file=sys.stderr)
        return 2

    root.mkdir(parents=True, exist_ok=True)
    for relative in PROJECT_DIRS:
        (root / relative).mkdir(parents=True, exist_ok=True)

    timestamp = now_iso()
    local_files = args.local_files
    if local_files is None:
        local_files = HOST_LOCAL_FILES[args.host]
    capabilities = {key: False for key in CAPABILITY_KEYS}
    capabilities["local_files"] = bool(local_files)
    data = {
        "schema_version": 1,
        "project_id": args.project_id or str(uuid.uuid4()),
        "title": args.title,
        "project_root": str(root),
        "host": {"name": args.host, "capabilities": capabilities},
        "current_stage": "START",
        "stage_status": "进行中",
        "pending_request": "Pick the run mode and the output aspect ratio for this project.",
        "next_stage": "BRIEF",
        "decisions": {},
        "artifacts": {},
        "stage_history": [],
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    state_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(state_path)
    return 0


def command_validate(args: argparse.Namespace) -> int:
    path = Path(args.state_file).expanduser().resolve()
    try:
        data = load_state(path)
    except ValueError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    errors = validate_state(data, path)
    if errors:
        for error in errors:
            print(f"INVALID: {error}", file=sys.stderr)
        return 1
    print("VALID")
    return 0


def command_repair(args: argparse.Namespace) -> int:
    path = Path(args.state_file).expanduser().resolve()
    try:
        data = load_state(path)
    except ValueError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1

    parent = path.parent.resolve()
    recorded = data.get("project_root")
    if isinstance(recorded, str) and Path(recorded).expanduser().resolve() == parent:
        print(f"OK: project_root already matches {parent}")
        return 0

    data["project_root"] = str(parent)
    data["updated_at"] = now_iso()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"REPAIRED: project_root set to {parent}")

    errors = validate_state(data, path)
    if errors:
        for error in errors:
            print(f"INVALID: {error}", file=sys.stderr)
        return 1
    return 0


def command_summary(args: argparse.Namespace) -> int:
    path = Path(args.state_file).expanduser().resolve()
    try:
        data = load_state(path)
    except ValueError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    errors = validate_state(data, path)
    if errors:
        for error in errors:
            print(f"INVALID: {error}", file=sys.stderr)
        return 1
    print(f"Project: {data['title']}")
    print(f"Host: {data['host']['name']}")
    print(f"Stage: {data['current_stage']} ({data['stage_status']})")
    print(f"Pending: {data['pending_request']}")
    print(f"Next: {data.get('next_stage') or '(none)'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="initialize a new project state")
    init_parser.add_argument("project_root")
    init_parser.add_argument("--title", required=True)
    init_parser.add_argument("--host", choices=HOSTS, required=True)
    init_parser.add_argument(
        "--local-files",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="override the host default for project-folder access",
    )
    init_parser.add_argument("--project-id")
    init_parser.set_defaults(func=command_init)

    validate_parser = subparsers.add_parser("validate", help="validate an existing state file")
    validate_parser.add_argument("state_file")
    validate_parser.set_defaults(func=command_validate)

    repair_parser = subparsers.add_parser(
        "repair", help="repoint project_root after the project folder was moved"
    )
    repair_parser.add_argument("state_file")
    repair_parser.set_defaults(func=command_repair)

    summary_parser = subparsers.add_parser("summary", help="print the current stage and pending request")
    summary_parser.add_argument("state_file")
    summary_parser.set_defaults(func=command_summary)

    return parser


def force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass


def main() -> int:
    force_utf8_output()
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
