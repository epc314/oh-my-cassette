from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.e2e
def test_weixin_e2e_harness_reports_latest_job():
    required = ["CASSETTE_E2E_JOB_ROOT", "CASSETTE_MEDIA_DIR"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        pytest.skip(f"missing E2E environment variables: {', '.join(missing)}")

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "e2e_weixin_cassette.py")],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=int(os.getenv("CASSETTE_E2E_TIMEOUT_SEC", "1800")) + 30,
        check=False,
    )
    assert proc.stdout.strip(), proc.stderr
    payload = json.loads(proc.stdout)
    assert {"success", "job_id", "status", "manifest_path", "result_path", "output_links", "errors"} <= payload.keys()
    assert "prompt" not in proc.stdout
    assert "asset_paths" not in proc.stdout
    assert "worker_command" not in proc.stdout
    if not payload["success"]:
        pytest.fail(f"E2E harness did not report success: {payload}")


@pytest.mark.e2e
def test_local_cassette_e2e_harness_runs():
    if not os.getenv("CASSETTE_URL"):
        pytest.skip("missing CASSETTE_URL")
    media = ROOT / "tests" / "fixtures" / "sample.mp4"
    if not media.exists():
        pytest.skip("missing tests/fixtures/sample.mp4")

    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "e2e_local_cassette.py"),
            "--media",
            str(media),
            "--instruction",
            "帮我剪成 10 秒以内的短视频，加中文字幕",
        ],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=int(os.getenv("CASSETTE_E2E_TIMEOUT_SEC", "1800")) + 30,
        check=False,
    )
    assert proc.stdout.strip(), proc.stderr
    payload = json.loads(proc.stdout)
    assert {"success", "job_id", "status", "manifest_path", "result_path", "output_links", "errors"} <= payload.keys()
    assert "prompt" not in proc.stdout
    assert "asset_paths" not in proc.stdout
    assert "worker_command" not in proc.stdout
    if not payload["success"]:
        pytest.fail(f"Local Cassette E2E harness did not report success: {payload}")
