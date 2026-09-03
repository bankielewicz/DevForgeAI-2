# research-core (temporary component)

Python implementation of the Research Core: P0-P9 state machine, evidence custody,
sealing, and the `devforgeai-research` CLI. Packaged from the root `pyproject.toml`
(`where = ["components/research-core/src"]`); run tests with
`PYTHONPATH=components/research-core/src python3 -m pytest tests/research -q`.

Status: staging for extraction. Per `docs/design/adr/ADR-0001-research-placement.md`,
Research is a deterministic capability of the protected DevForge product. This package
moves to that repository (as a `devforge-research` module, later a Rust crate) once the
public error taxonomy, CLI contract and language-neutral conformance fixtures exist.
Packaging metadata stays at the repository root until extraction begins. The installer
never copies this directory into a target project; the wheel is installed separately.
