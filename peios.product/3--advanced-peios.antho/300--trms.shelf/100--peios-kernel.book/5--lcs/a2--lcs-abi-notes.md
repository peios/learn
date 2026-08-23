---
title: LCS ABI Notes
description: What the LCS ABI tables cannot say for themselves — which properties of the interface are documented with their operations rather than here, and the kernel configuration LCS is built by.
---

§5.A is generated from `pkm/uapi/pkm/lcs.h` and holds only what a
compiler can measure. This appendix holds the rest.

The split is structural rather than editorial. `gen-lcs-abi.py`
overwrites §5.A wholesale on every run, so anything written there is
lost the next time the ABI changes.

## What is not here

The header carries names, numbers and layouts. Everything else about the
interface is a property of the implementation rather than of the ABI, and
is documented with the operation it belongs to: the required access right
for each ioctl and the two-pass output buffer convention in §5.6, the
error vocabulary in §5.6.4, the RSI payload shapes in the Registry Source
Interface specification, and the backup stream's record payloads in the
Registry Backup Format specification.

`REG_BACKUP_MAGIC` in §5.A is the eight-byte header magic; the record type
codes are the framing, not the payloads.

## Build configuration

LCS is built by `CONFIG_SECURITY_PKM`, a boolean option, so it is linked
into `vmlinux` rather than loaded. `CONFIG_RUST=y` is required: the
resolution core, the RSI codec, the backup serialiser and the transaction
log are Rust, staged into the kernel tree as `security/pkm/lcs/lcs_core`.
`CONFIG_SECURITY_PKM_KUNIT` compiles in the in-kernel test harness.

The three syscall numbers are added to the syscall table by
`kernel/patches/arch/syscall-table-pkm.patch`, which patches both
`arch/x86/entry/syscalls/syscall_64.tbl` and the copy of it that ships
under `tools/perf/`. They are registered `common`, so they are reachable
from the x32 ABI as well as from x86-64.
