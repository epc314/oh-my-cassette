from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


SENSITIVE_KEYS = {
    "prompt",
    "prompt_redacted",
    "asset_paths",
    "worker_command",
    "chat_id",
    "user_id",
    "message_id",
    "wxid",
}
TERMINAL_STATUSES = {"succeeded", "failed", "needs_user", "timed_out", "timeout", "cancelled"}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_cassette_package() -> None:
    if "cassette" in sys.modules:
        return
    root = repo_root()
    spec = importlib.util.spec_from_file_location(
        "cassette",
        root / "__init__.py",
        submodule_search_locations=[str(root)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["cassette"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def json_stdout(payload: dict[str, Any]) -> None:
    print(json.dumps(scrub(payload), ensure_ascii=False, sort_keys=True))


def scrub(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if key in SENSITIVE_KEYS:
                continue
            cleaned[key] = scrub(item)
        return cleaned
    if isinstance(value, list):
        return [scrub(item) for item in value]
    return value


def safe_error_codes(errors: Any) -> list[dict[str, str]]:
    safe: list[dict[str, str]] = []
    if not isinstance(errors, list):
        return safe
    for error in errors:
        if not isinstance(error, dict):
            continue
        code = str(error.get("code") or "unknown_error")
        safe.append({"code": code})
    return safe


def output_links(job: dict[str, Any]) -> list[str]:
    links: list[str] = []
    for output in job.get("outputs") or []:
        if not isinstance(output, dict):
            continue
        if output.get("downloaded") and output.get("filename"):
            links.append(str(output["filename"]))
        elif output.get("href"):
            links.append(str(output["href"]))
    return links


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def latest_job_file(*roots: Path) -> Path | None:
    candidates: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        if root.is_file() and root.name.startswith("cassette_") and root.suffix == ".json":
            candidates.append(root)
            continue
        candidates.extend(path for path in root.rglob("cassette_*.json") if path.is_file())
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def find_session_manifest(job: dict[str, Any], *roots: Path) -> str:
    explicit = job.get("manifest_path")
    if isinstance(explicit, str) and explicit:
        return explicit
    session_hash = job.get("session_hash")
    if not isinstance(session_hash, str) or not session_hash:
        return ""
    for root in roots:
        if not root.exists():
            continue
        direct = root / "sessions" / session_hash / "manifest.json"
        if direct.exists():
            return str(direct)
        for path in root.rglob("manifest.json"):
            data = read_json(path)
            if data and data.get("session_hash") == session_hash:
                return str(path)
    return ""


def wait_for_latest_job(
    roots: list[Path],
    timeout_sec: int,
) -> tuple[Path | None, dict[str, Any] | None, bool]:
    deadline = time.monotonic() + timeout_sec
    latest_path: Path | None = None
    latest_data: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        candidate = latest_job_file(*roots)
        if candidate is not None:
            data = read_json(candidate)
            if data:
                latest_path = candidate
                latest_data = data
                status = str(data.get("status") or "")
                if status in TERMINAL_STATUSES:
                    return latest_path, latest_data, False
        time.sleep(2)
    return latest_path, latest_data, True
