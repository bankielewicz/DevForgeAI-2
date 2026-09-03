# framework/contracts

Machine-readable contracts the runtime reads and the documents cite. Nothing under `docs/` is installed into a target project, so anything a hook, the sequencer or a worker must agree on at run time lives here.

| File | Purpose | Validated by |
|---|---|---|
| `error-taxonomy.yaml` | The closed vocabulary of every outcome the framework reports, with emitter, protocol, roll-up and recovery route per code | `schemas/devforgeai/v1/error-taxonomy.schema.json` |
| `PROMOTION-CANDIDATE.md` | What a human reviews and promotes into the protected DevForge repository as contract v1, with the verification commands | reviewer |
| `MANIFEST.sha256` | Digests of the candidate files plus the two pinned document sections; `sha256sum -c` verifies | `sha256sum -c`, `verify.py --only v3` |

## Install guidance for the future installer

`install-manifest.yaml` lists this directory as its first entry (`order: 1`, `verbatim: true`, `pin_digest: true`):

```yaml
- source: framework/contracts
  destination: .devforgeai/contracts
```

Rules the installer must honour for this tree:

- Copy verbatim. Contracts are data, never templated or merged.
- Install before hooks and skills. The hook runtime and the sequencer read `.devforgeai/contracts/error-taxonomy.yaml` at start; a missing file is a `could_not_run` for `phase start`, not a silent default.
- Pin by digest. Record the file's sha256 in `.devforgeai/state.yaml#contracts` so `devforgeai validate` can detect a hand-edited copy.
- Version, do not patch. A change ships as a new `taxonomy_version`; an installed project upgrades by reinstalling the tree, never by editing in place.
- Uninstall removes the tree only when no run is `active` or `ready_to_promote`.

## Status

`error-taxonomy.yaml` is a draft (`taxonomy_version: 1`, 2026-09-03). Its codes are the ones documents 09 and 10 already use; the new parts are the phase-outcome roll-up and the hook failure classes. Its `open_items` list the divergences to close before version 2. The narrative is `docs/design/13-error-taxonomy.md`, which is not installed and is not normative.
