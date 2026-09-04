from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "pr-verify.yml"
LOCK = ROOT / "uv.lock"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


def load_workflow() -> tuple[str, dict[str, object]]:
    text = WORKFLOW.read_text(encoding="utf-8")
    loaded = yaml.safe_load(text)
    assert isinstance(loaded, dict)
    return text, loaded


def test_workflow_has_no_privileged_trigger_secret_or_write_permission() -> None:
    text, workflow = load_workflow()
    base_loaded = yaml.load(text, Loader=yaml.BaseLoader)
    assert set(base_loaded["on"]) == {"pull_request", "push"}
    assert base_loaded["on"]["push"]["branches"] == ["main"]
    assert "pull_request_target" not in text
    assert "secrets." not in text
    assert "permissions: write-all" not in text
    assert "git push" not in text
    assert "gh api" not in text
    assert workflow["permissions"] == {"contents": "read"}


def test_every_action_reference_is_an_immutable_commit() -> None:
    _, workflow = load_workflow()
    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    references = [
        step["uses"]
        for job in jobs.values()
        for step in job.get("steps", [])
        if "uses" in step
    ]
    assert references
    for reference in references:
        _, separator, revision = reference.rpartition("@")
        assert separator == "@"
        assert FULL_SHA.fullmatch(revision), reference


def test_checkout_uses_the_exact_event_head() -> None:
    text, _ = load_workflow()
    assert "github.event.pull_request.head.sha || github.sha" in text
    assert text.count("ref: ${{ github.event.pull_request.head.sha || github.sha }}") >= 4


def test_verification_jobs_and_fail_closed_aggregate_are_present() -> None:
    _, workflow = load_workflow()
    jobs = workflow["jobs"]
    required = {"research", "contracts", "sequencer", "release_candidate", "required"}
    assert required <= set(jobs)
    aggregate = jobs["required"]
    assert aggregate["if"] == "${{ always() }}"
    assert set(aggregate["needs"]) == required - {"required"}
    command = aggregate["steps"][0]["run"]
    for job in required - {"required"}:
        assert f"needs.{job}.result" in command


def test_python_environment_is_reproduced_from_the_lock() -> None:
    text, _ = load_workflow()
    assert LOCK.is_file()
    assert "uv sync --frozen --dev" in text
    assert 'UV_PYTHON: "3.12.3"' in text
    assert 'UV_PYTHON_DOWNLOADS: "never"' in text
    assert "pip install" not in text
    assert "uv.lock" in text
    assert "uv run python -m pytest tests/research -q" in text
    assert "uv run pytest" not in text
    assert "uv build --no-build-isolation" in text


def test_release_candidate_is_verified_but_never_installed() -> None:
    text, _ = load_workflow()
    assert "components/devforge-release/tests" in text
    assert "components/devforge-release/launcher/build.sh" in text
    assert "components/devforge-release/launcher/BUILD-DIGEST.txt" in text
    assert "components/devforge-release/install.sh" not in text
    assert "sudo " not in text
    assert "/usr/local" not in text
