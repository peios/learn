---
title: CLI Reference
type: reference
description: Complete reference for the provium command-line interface — test execution, filtering, parallelism, and resource management.
---

## Commands

### provium test

Discovers and runs test files.

```
provium test [options] <path>
```

The `path` argument is a directory containing `.lua` test files, or a single `.lua` file. Provium walks directories recursively, collecting all `.lua` files except those in `fixtures/` subdirectories.

### provium version

Prints the version number.

```
provium version
```

## Test options

| Flag | Description |
|---|---|
| `-p N` | Run N tests in parallel. Default: auto (half the CPU count, minimum 2). |
| `-f pattern` | Only run tests whose filename contains `pattern`. Repeatable — a test runs if it matches any filter. |
| `--fail-fast` | Stop launching new tests after the first failure. Tests already running continue to completion. |
| `--rerun-failed` | Rerun tests that failed in the most recent run. Reads failure logs from `/tmp/provium-runs/`. |
| `--mem N` | Total memory budget for VMs. Accepts suffixes: `512M`, `4G`. Enables fixed resource pooling. |
| `--cpus N` | Total CPU budget for VMs. Enables fixed resource pooling. |

## Examples

Run all tests in a directory:

```bash
provium test tests/
```

Run a single test file:

```bash
provium test tests/kacs_boot.lua
```

Filter by filename:

```bash
provium test -f token -f session tests/
```

Run sequentially (no parallelism):

```bash
provium test -p 1 tests/
```

Stop on first failure:

```bash
provium test --fail-fast tests/
```

Rerun failures from the last run:

```bash
provium test --rerun-failed tests/
```

Run with a fixed resource budget:

```bash
provium test --mem 4G --cpus 8 tests/
```

## Output format

```
provium test

  kacs_boot.lua ... ok (2.1s)
  kacs_token.lua ... ok (86 tests, 4.3s)
    · open_self_token_returns_fd ... ok
    · open_self_token_no_privilege_required ... ok
    · ...
  kacs_access_check.lua ... FAIL (3.2s)
    · basic_allow ... ok
    · deny_ace_evaluated_first ... FAIL: expected 0, got -13
    command failed (exit 1): ...
    --- console (last 20 lines) ---
    ...

Failed test logs:
  kacs_access_check.lua                    → /tmp/provium-runs/run-abc123/kacs_access_check.lua.log

FAIL: 2 passed, 1 failed
```

Each test file shows:

- **Name** and **status** (`ok` or `FAIL`)
- **Duration** and **sub-test count** (if `test()` blocks are used)
- **Sub-test details** (individual pass/fail/todo for each)
- **Error message** and **console tail** (on failure)

On failure, the log file path is printed so you can inspect full QEMU console output.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | All tests passed |
| 1 | One or more tests failed, or an error occurred |

## Parallelism

By default, Provium runs tests in parallel using auto-detection:

- **Concurrency:** Half the CPU count (minimum 2)
- **Memory gating:** Checks `/proc/meminfo` MemAvailable before launching each VM, keeping 1.5 GB free for the host

With `--mem` and/or `--cpus`, Provium switches to fixed resource pooling: VMs acquire from the declared budget and block if resources are exhausted. This gives deterministic scheduling at the cost of potentially under-utilizing available hardware.

With `-p 1`, tests run sequentially with no parallelism.

See [Resource Management](~provium/configuration/resource-management) for details on how resource pooling works.
