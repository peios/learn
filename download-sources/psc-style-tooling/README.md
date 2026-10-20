# Peios style tooling

Pinned configuration bundle for [PSC](https://learn.peios.org/psc/).
It qualifies formatting and selected checks in isolated fixtures.
It does not automatically scan, rewrite or enforce style across repositories.

## Run

From this directory:

```sh
python3 scripts/bootstrap.py
python3 scripts/qualify.py
```

To add read-only wrapper samples and kernel-provenance comparison, pass
`--kernel /absolute/path/to/kernel`. Without that option, the included kernel
formatter snapshots still receive fixture checks. A changed kernel baseline
needs a reviewed provenance update before the optional comparison passes.

The bootstrap creates `.venv`, `node_modules`, `.bin` and `.cache` locally.
Python wheels are hash-locked; npm uses its integrity lock with lifecycle scripts
disabled; release binaries have pinned artifact and executable hashes. It checks
host runtime versions and fails on drift rather than silently changing versions.
It does not install or change the host runtime toolchains.

The pinned host profile is Linux x86_64, CPython 3.14.4, Node 22.22.1,
npm 9.2.0, Go 1.26.0 and Rust 1.98.1 with rustfmt and Clippy. Kernel formatting
also requires rustfmt from Rust 1.83.0, matching the kernel build toolchain.
These are qualification-host pins, not minimum language versions for Peios
components. Other hosts need separately resolved artifacts and qualification.
This pins development tools; it is not a hermetic operating-system image.

## Tool versions

| Tool | Version |
| --- | --- |
| clang-format / clang-tidy | 18.1.8 |
| Ruff | 0.17.0 |
| mypy | 2.4.0 |
| Prettier | 3.9.10 |
| ESLint | 10.12.0 |
| typescript-eslint | 8.71.2 |
| TypeScript | 6.0.3 |
| shfmt | 3.14.1 |
| ShellCheck | 0.11.0 |
| buildifier | 10.1.0 |

TypeScript 6.0.3 is intentional: the pinned typescript-eslint supports TypeScript
below 6.1. Selecting the newer TypeScript release would exceed that support range.
clang 18 matches the existing kernel LLVM major. Complete transitive Python/npm
pins and binary hashes live in the adjacent lockfiles.

Each dependency has a specific job: native language formatters handle layout;
Ruff/mypy and ESLint/TypeScript provide complementary lint and type checks;
ShellCheck and buildifier understand their respective command/build languages.
The small local ESLint rule fills a demonstrated mismatch with the agreed brace
policy. No runtime dependency is added to a shipped Peios component by this bundle.

## Settings and scope

Common layouts use four spaces and a 100-column target, subject to language
exceptions. Go uses gofmt; the kernel snapshots retain their own C/Rust settings.
Python/JavaScript prefer double quotes when semantically interchangeable and use
alternative quoting to reduce escapes. JavaScript/TypeScript uses semicolons.
Python imports are grouped by Ruff's import checker. Other language import groups
are preserved/reviewed rather than automatically reordered across side effects.

The Python syntax target is 3.11 and Rust fixture edition is 2021. TypeScript's
fixture targets ES2022 with bundler resolution. These are explicit fixture/profile
settings: component integration must select its actual runtime, edition, module
system, globals, source roots and third-party stubs. In particular, do not copy
bundler resolution into a Node component without checking that component's needs.

`configs/editorconfig` is a common template, not a kernel-root configuration.
Do not apply its four-space settings over inherited Linux code. Use the kernel
profile and ownership-specific scopes described in the kernel exception guide.

Generated and vendored files are excluded by the Ruff/ESLint templates and the
Prettier ignore template. Tools without equivalent exclusions must receive an
explicit owned-file list. Never use a blanket recursive source rewrite as the
cutover command. Automatic naming fixes must preserve public/serialized contracts.

## Selected checks

- C: core analyzer checks, duplicate includes, isolated declarations, and a partial
  brace check. Qualification promotes selected warnings with `--warnings-as-errors=*`.
- Rust: compiler checks and `clippy::correctness`; no blanket pedantic or all-warning
  failure policy. Kernel source compilation retains the kernel's own build checks.
- Go: `go vet` and normal compiler checks.
- Python: basic syntax/name/import checks and ordinary function annotations, plus
  mypy's annotation/type checks. No hard line-length, complexity or wildcard-import ban.
- JavaScript/TypeScript: the local brace rule, duplicate/unreachable/unused-code
  checks, `prefer-const`, explicit-any checking and TypeScript strict checking.
- Shell: ShellCheck using the script's stated dialect; shfmt with four-space indents.
- Starlark: buildifier formatting and `load`, `unused-variable`, `function-docstring`
  warnings. This does not enable every buildifier warning or migrate Bazel APIs.

Narrow, explained exceptions remain possible. For side-effect-sensitive Python
imports, preserve order with a documented isort exclusion; do not run import fixes
blindly. Keep unused-suppression diagnostics where configured.

## Limits that remain review responsibilities

clang-tidy 18's short-statement brace option counts from the end of the condition.
It misses a multiline condition with a same-line body and does not enforce the
whole-chain rule. The suite deliberately demonstrates those gaps. The common
100-column eligibility for C brace omission also needs review. Kernel C follows
its separate Linux brace policy; do not apply the common C checker to it.

The JavaScript/TypeScript rule checks the whole clause, its 100-column eligibility,
and conditional chains without requiring all optional braces. It is diagnostic
only: it never rewrites control flow. It counts source characters with expanded
tabs for the eligibility boundary, not terminal-specific glyph display widths.

The 50-line function and three-level nesting thresholds are review prompts, not
hard failures. Meaningful names, dependency choices, ownership, API compatibility
and expected performance improvements also require review. Formatter success is
not evidence that those requirements have been met.

## Verify the bundle and run checks

Run `sha256sum -c MANIFEST.sha256` to check the distributed source files.
The runner writes `results/qualification.json` with results, runtime/tool
versions and sample source hashes. Qualification covers
formatter idempotence, policy accept/reject cases, typed failures, narrow
suppressions, exclusion handling and selected analyzer/compiler checks.

With `--kernel`, the runner formats copies of six Peios wrappers in memory and
checks that their source bytes did not change. It reports which would need
formatting at cutover; it does not claim the wrappers already comply. Kernel C
and Rust configuration snapshots are tied to `kernel-provenance.json`.

The test runner intentionally keeps the fixture sequence together despite the
soft function-length threshold: its linear setup/check/report flow is reviewed
as test orchestration rather than enforcing the threshold as a hard limit.

The kernel maintains an adapted subset with scoped formatting, Bazel checks,
and a workflow in `peios/style/` within its repository. Components integrate
their selected profiles separately. Passing this fixture suite does not qualify
a component's build or CI execution. Historical qualification reports are kept
outside the published source bundle.
