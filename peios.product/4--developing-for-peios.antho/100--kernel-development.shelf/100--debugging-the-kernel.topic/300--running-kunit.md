---
title: Running KUnit
type: guide
description: Boot an already-built KUnit kernel and distinguish passing test cases from a clean kernel qualification run.
related:
  - peios/debugging-the-kernel/overview
  - peios/debugging-the-kernel/kernel-tracepoints
---

From a PKM checkout, `build/test-kunit.sh` boots an already-built kernel in QEMU and checks its serial log. Supply either a kernel build tree or its `bzImage`. The kernel must include KUnit and the PKM test suites; enable `CONFIG_PROVE_LOCKING` when investigating lock ordering.

```sh
build/test-kunit.sh /path/to/bzImage
```

The runner requires successful emulator exit, clean power-down, and complete top-level KTAP results. An unfiltered run must also contain PKM's smoke marker and a passing PKM suite summary. A timeout, failed assertion, kernel warning, panic, or diagnostic that disables lock checking fails the run even when the individual test cases report success. Read the retained serial log for the cause: passing assertions alone do not establish that lock checking stayed active.

## Selecting tests

`PKM_KUNIT_FILTER` passes a KUnit suite/test glob to the kernel. For example:

```sh
PKM_KUNIT_FILTER='pkm_kunit_file.*' build/test-kunit.sh /path/to/bzImage
```

A filtered run may omit the global smoke test or select an upstream single-case suite without an aggregate summary. It must still emit selected case results, complete its top-level KTAP plan, and power down cleanly. Selecting no cases is a failure. Kernel diagnostic checks remain enabled for filtered runs.

## Logs and emulator settings

| Variable | Purpose |
| --- | --- |
| `PKM_KUNIT_LOG` | Override the serial-log path; by default, `kunit-qemu.log` is written beside the supplied image or inside the supplied build tree. |
| `PKM_KUNIT_TIMEOUT` | Emulator timeout in seconds, defaulting to 420. |
| `PKM_KUNIT_INITRD` | Optional initrd path. |
| `QEMU_BIN` | Emulator executable, defaulting to `qemu-system-x86_64`. |

The script does not build, sign, install, or publish a kernel. Its result applies to the image and selected tests that were actually run; native integration suites and hardware qualification are separate checks.
