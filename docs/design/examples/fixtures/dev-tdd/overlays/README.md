# Eval overlays

Copy `../` (the base fixture) to a scratch directory, then copy the matching overlay
on top of it before running the eval prompt:

| Eval | Overlay | Effect |
|------|---------|--------|
| 1 | none | base fixture |
| 2 | `eval-2/` | criterion 3 carries an unresolved ASSUMPTION tag |
| 3 | `eval-3/` | criterion 1 already has a real passing test and a minimal slugify; criteria 2 and 3 still fail |

## eval-done

A completed implementation of STORY-001 (all three criteria green). Used as the passing-path input for review and qa evals so they do not depend on running the sequencer demo first. Apply over a fresh fixture copy: `cp -r overlays/eval-done/. <copy>/`.
