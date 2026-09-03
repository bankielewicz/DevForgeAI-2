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
      Tests live under tests/ and are named <module>.test.mjs. They run on the
      node:test runner in the standard library; no test framework is installed
      and no test may import from outside the package under test.
  - source: docs/architecture/sourcetree.md#packages
    status: OBSERVED
    hash: sha256:fixture0000000000000000000000000000000000000000000000000000000003
    excerpt: |
      tinyapp/            application package (ES modules)
      tinyapp/text.mjs    text helpers (currently empty)
      tests/              test suite
write_fence:
  - tinyapp/text.mjs
  - tests/text.test.mjs
commands:
  source: .devforgeai/stack.yaml#node
  hash: sha256:fixture0000000000000000000000000000000000000000000000000000000004
  use: [test, lint]
test_plan:
  - criterion: 1
    file: tests/text.test.mjs
    name: test_slugify_basic
  - criterion: 2
    file: tests/text.test.mjs
    name: test_slugify_unicode
  - criterion: 3
    file: tests/text.test.mjs
    name: test_slugify_empty
---

# STORY-001: Add slugify helper

## Goal

Provide `slugify(title: string) -> string`, exported from `tinyapp/text.mjs`, so page titles can become URL-safe path segments.

## Context

See the frontmatter context bundle. `tinyapp/text.mjs` exists and exports nothing. `tests/text.test.mjs` does not exist.

## Interface

```js
// tinyapp/text.mjs
export function slugify(title) { /* ... */ }
```

Pure function. Never throws for a string argument. No other export is added.

## Acceptance Criteria

1. `slugify("Hello, World!")` returns `"hello-world"`: lowercase, non-alphanumerics collapsed to single hyphens, no leading or trailing hyphen.
2. `slugify("  Ünïcödé  Tïtle ")` returns `"unicode-title"`: accents are stripped to ASCII before slugging.
3. `slugify("")` and `slugify("!!!")` both return `""` rather than throwing.

## Unchanged Behaviour

None.

## Out of Scope

- Transliteration of non-Latin scripts.
- A maximum length parameter.

## Verification

- Red: `test` exits non-zero; `test_slugify_basic`, `test_slugify_unicode`, `test_slugify_empty` each fail on an assertion, not on module resolution.
- Green: `test` exits zero; only `tinyapp/text.mjs` changed since red.
- Refactor: `test` and `lint` exit zero; no file outside the write fence changed.
- QA (light): `test` exits zero; the critic confirms no test asserts a constant.

## Clarifications

None.
