---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: stack
template_version: 1
accepts_versions: [1]
required_frontmatter: [version, compiled, package_manager, manifests, ignore_dirs, commands, test_glob, test_layout, runner_probe, packages, extractors, forbidden_imports]
required_sections: ["## Identity", "## Commands", "## Tests", "## Packages", "## Forbidden Imports"]
id_pattern: "^[a-z][a-z0-9-]*$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# required_sections derived: 11's row records only that this is not a Markdown artifact, so the five
#   sections are the key groups of the section contract in 10-sequencer-and-contracts.md section 7 -
#   identity (version, compiled, package_manager, manifests, ignore_dirs), commands, tests (test_glob, test_layout,
#   runner_probe), packages plus extractors, and forbidden_imports.
# render: the instance frontmatter is one section of .devforgeai/stack.yaml, installed under an anchor
#   name matching id_pattern; a story pins the whole file by hash and names that anchor
#   (10 section 7). The body is the design-time explanation of each key, not part of the installed YAML.
# install: .devforgeai/stack.yaml is a producer-exception path: it is in architect's and onboard's
#   document fences and in no other skill's. Architect's techstack phase writes the INTENDED section and
#   onboard's code_map phase writes the OBSERVED one, both inside the candidate root; the sequencer
#   validates the file against schemas/devforgeai/v1/stack.schema.json before the run is promoted
#   (10 section 7, 11 divergence 5).
# id_pattern applies to the anchor name the section is installed under.
# provenance: carried by `depends_on:` - the techstack.md sections this section is the executable side
#   of (INTENDED) and the manifests it was read from (OBSERVED), per 11 section 3. techstack.md points
#   the other way through `stack_section`, and /drift resolves both to notice a divergence.
# == instance frontmatter: fill every field ==
version: 1
compiled: false             # true requires commands.build, and the oracle runs it before test
package_manager: "{{manifest ecosystem}}"
manifests:
  - "{{manifest glob}}"
ignore_dirs:                # root-relative dirs excluded from copy-mode candidate roots and tree hashing
  - "{{build output dir}}"
commands:
  test:                     # mandatory; every other key is optional
    argv: ["{{program}}", "{{arg}}"]
    cwd: "."
    junit_path: ".devforgeai/work/junit.xml"
    timeout_s: 600
  lint:
    argv: ["{{program}}", "{{arg}}"]
    timeout_s: 600
test_glob: "{{test glob}}"
test_layout: "{{placement convention}}"
runner_probe:
  argv: ["{{program}}", "--version"]
  exit_ok: 0
packages:
  allow: ["{{package name}}"]
  deny: ["{{regex}}"]
extractors:
  - paths: ["{{manifest glob}}"]
    regex: "{{regex with capture group 1 as the package name}}"
forbidden_imports:
  - paths: ["src/{{package}}/**"]
    patterns: ["{{import pattern}}"]
    reason: "{{quoted verbatim in the refusal}}"
depends_on:                 # re-resolved by /drift and /amend
  - source: "docs/architecture/techstack.md#testing"
    hash: sha256:{{64 hex}}
  - source: "{{manifest path}}"
    hash: sha256:{{64 hex}}
---

# Stack Section: {{anchor}}

## Identity

`version` is the section contract version. `compiled` decides whether `commands.build` is required and run before every test. `package_manager` names the ecosystem, and `manifests` lists the only files scanned for dependency policy. `ignore_dirs` lists root-relative directories the sequencer excludes when it materialises a copy-mode candidate root and when it hashes the tree for a checkpoint manifest: build output, caches, virtual environments. `.git` and `.devforgeai/work` are excluded whether or not they are listed.

## Commands

One entry per key the sequencer may broker: `build`, `test`, `lint`, `format`, with `test` mandatory. `argv` is exec form and is launched without a shell, so a redirect, pipeline or variable in it is text, not syntax.

## Tests

`test_glob` says where tests live and `test_layout` names the placement convention a red phase must follow. `runner_probe` is the cheap liveness check whose miss is `runner_missing`, not a phase failure.

## Packages

`packages.allow` is exact names compared case-insensitively against every name an extractor captures; `packages.deny` is regexes matched against manifest text. `extractors` must each capture the package name in group 1.

## Forbidden Imports

One entry per source-level ban, scoped by `paths`. The `reason` string is quoted verbatim in the refusal, so write it as the sentence the developer should read.
