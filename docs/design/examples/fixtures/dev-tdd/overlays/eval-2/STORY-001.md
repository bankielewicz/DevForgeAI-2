---
id: STORY-001
epic: EPIC-001
sprint: sprint-001
scope: feature
status: ready
template: story
template_version: 3
requires_skill: dev-tdd
risk_tier: LOW
size: S
gate_policy:
  unresolved_assumption: BLOCK
  stale_hash: BLOCK
  unresolvable_source: BLOCK
  write_fence_violation: BLOCK
  test_runner_missing: REQUIRE_HUMAN
  criterion_without_test: BLOCK
blocked_by: []
provenance:
  - source: docs/plan/tinyapp/epics/EPIC-001.md#story-001
    hash: sha256:fixture0000000000000000000000000000000000000000000000000000000000
context:
  - source: docs/architecture/constitution.md#mandates
    status: INTENDED
    hash: sha256:fixture0000000000000000000000000000000000000000000000000000000001
    excerpt: |
      tdd: required. Every behaviour change starts with a failing test.
      Production code is written only to make a failing test pass.
  - source: docs/architecture/techstack.md#testing
    status: INTENDED
    hash: sha256:fixture0000000000000000000000000000000000000000000000000000000002
    excerpt: |
      Tests live under tests/ and are named test_<module>.<ext>. No test may
      import from outside the package under test.
  - source: docs/architecture/sourcetree.md#packages
    status: OBSERVED
    hash: sha256:fixture0000000000000000000000000000000000000000000000000000000003
    excerpt: |
      tinyapp/            application package
      tinyapp/text.py     text helpers (currently empty)
      tests/              test suite
write_fence:
  - tinyapp/text.py
  - tests/test_text.py
commands:
  source: .devforgeai/stack.yaml#python
  hash: sha256:fixture0000000000000000000000000000000000000000000000000000000004
  use: [test, lint]
test_plan:
  - criterion: 1
    file: tests/test_text.py
    name: test_slugify_basic
  - criterion: 2
    file: tests/test_text.py
    name: test_slugify_unicode
  - criterion: 3
    file: tests/test_text.py
    name: test_slugify_empty
---

# STORY-001: Add slugify helper

## Goal

Provide `tinyapp.text.slugify(title: str) -> str` so page titles can become URL-safe path segments.

## Context

See the frontmatter context bundle. `tinyapp/text.py` exists and is empty apart from a module docstring. `tests/test_text.py` does not exist.

## Interface

```python
# tinyapp/text.py
def slugify(title: str) -> str: ...
```

Pure function. No other public name is added.

## Acceptance Criteria

1. `slugify("Hello, World!")` returns `"hello-world"`: lowercase, non-alphanumerics collapsed to single hyphens, no leading or trailing hyphen.
2. `slugify("  Ünïcödé  Tïtle ")` returns `"unicode-title"`: accents are stripped to ASCII before slugging.
3. ASSUMPTION: empty input behaviour is undecided.

## Unchanged Behaviour

None.

## Out of Scope

- Transliteration of non-Latin scripts.
- A maximum length parameter.

## Verification

- Red: `test` exits non-zero; `test_slugify_basic`, `test_slugify_unicode`, `test_slugify_empty` each fail on an assertion, not on import.
- Green: `test` exits zero; only `tinyapp/text.py` changed since red.
- Refactor: `test` and `lint` exit zero; no file outside the write fence changed.
- QA (light): `test` exits zero; the critic confirms no test asserts a constant.

## Clarifications

None.
