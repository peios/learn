---
title: Style Tooling
type: how-to
description: Download and use the shared style configurations and qualification fixtures.
related:
  - psc/scope-and-precedence
  - psc/common-coding-rules/formatting
---

The style tooling bundle supplies pinned formatter and checker configurations,
setup scripts, and fixtures for the PSC language profiles. Component
maintainers select the applicable parts and integrate them with their own
build and CI commands.

## Download the bundle

- [Download PSC Style Tooling](~attachments/psc-style-tooling).
- [Download metadata and SHA-256 checksum](~attachments/psc-style-tooling/metadata).

The metadata records the archive's exact byte size and SHA-256 digest. Compare
the downloaded file's digest with that record before unpacking it:

```sh
sha256sum psc-style-tooling.tar.gz
tar -xzf psc-style-tooling.tar.gz
cd psc-style-tooling
sha256sum -c MANIFEST.sha256
```

The archive contains configurations, scripts, fixtures, and dependency locks.
It excludes installed tools, caches, and local qualification results. The
download is rebuilt from the source bundle when its contents change.

## Prepare the required host

Read `runtimes.lock.json` before running the scripts. The bundle pins Linux
x86_64, Python 3.14.4, Node.js 22.22.1, npm 9.2.0, Go 1.26.0, Rust 1.98.1,
and the Rust 1.83.0 formatter for the kernel fixtures. These are fixture-host
requirements, not minimum versions for Peios components.

The bootstrap checks those versions. It fails on a mismatch and does not
install or replace the host runtime toolchains. Use a matching environment
to run the complete suite; reviewing or copying a configuration does not
require bootstrapping every language tool.

```sh
python3 scripts/bootstrap.py
python3 scripts/qualify.py
```

The bootstrap installs pinned tools beneath `.venv`, `node_modules`, `.bin`,
and `.cache`. It verifies download hashes and disables npm lifecycle scripts.
The qualification runner checks formatting stability, accepted and rejected
syntax, narrow suppressions, exclusions, and selected compiler diagnostics.
It writes the result to `results/qualification.json`.

For optional checks against a kernel checkout, supply its actual path:

```sh
python3 scripts/qualify.py --kernel /absolute/path/to/kernel
```

That mode checks the recorded kernel configuration hashes and formats copies
of selected wrappers. It does not rewrite the kernel checkout. A changed
kernel baseline needs a reviewed provenance update before those checks pass.

## Integrate a component

1. Select the configurations for the component's languages. Keep their exact
   tool versions and required lockfile entries together.
2. Set the actual source roots, language edition, runtime, module system,
   globals, and third-party stubs. The TypeScript fixture uses ES2022 and
   bundler resolution; that is not a default for Node.js applications.
3. List owned files explicitly. Exclude generated and imported code from
   formatting while retaining appropriate build and correctness checks.
4. Run the component's tests after formatting and checker changes. Add the
   same commands to developer workflows and CI.

The common EditorConfig template uses four spaces. Do not apply it over
inherited Linux code; the kernel retains its scoped formatting conventions.
The JavaScript brace checker is diagnostic only and does not rewrite control
flow.

## Keep manual review

Formatters do not establish API compatibility, ownership, naming quality, or
performance. The function-length and nesting thresholds remain review prompts.
Do not turn them into blanket build failures.

The pinned clang-tidy checks do not cover every multiline-condition or
mixed-chain brace case. C brace eligibility and those gaps still need review.
Use narrow, explained suppressions for justified exceptions, and preserve
side-effect-sensitive import order.
