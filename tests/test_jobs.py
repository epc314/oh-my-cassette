from __future__ import annotations

from cassette import jobs


def test_job_create_status_cancel(cassette_env):
    job = jobs.create_job("sess", "prompt text", "instruction", ["/tmp/a.mp4"], {"url": "https://example.test"})
    assert job["status"] == "queued"
    loaded = jobs.load_job(job["job_id"])
    assert loaded["prompt"] == "prompt text"
    assert loaded["prompt_redacted"].startswith("<redacted:")

    listed = jobs.list_jobs("sess")
    assert listed[0]["job_id"] == job["job_id"]
    assert "prompt" not in listed[0]
    assert "asset_paths" not in listed[0]

    cancelled = jobs.request_cancel(job["job_id"])
    assert cancelled["status"] == "cancel_requested"
    assert cancelled["finished_at"] is None
    assert jobs.is_cancel_requested(job["job_id"]) is True
