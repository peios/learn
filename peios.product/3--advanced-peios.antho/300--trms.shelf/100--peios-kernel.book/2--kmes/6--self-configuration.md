---
title: Self-Configuration
description: The four parameters KMES reads from the registry, how it bootstraps before LCS exists, and the watch that keeps them current.
---

KMES reads four operational parameters from the registry under
`Machine\System\KMES\`. Compiled-in defaults carry it from module load
until LCS becomes available; from then on a persistent kernel-internal
watch keeps it current. The key names, types, defaults, and ranges are
in §2.A.

At no point does KMES wait for configuration. The defaults are always
sufficient, and if LCS never appears KMES runs on them indefinitely.

## Reading and validating

Value names are matched with LCS's value-name comparison rules —
Unicode Simple Case Folding, case-preserving and case-insensitive.
Names in the subtree that do not fold to one of the four canonical
names are unknown keys: they are counted and ignored.

A `REG_DWORD` value carries exactly four little-endian payload bytes
and a `REG_QWORD` exactly eight. A value whose type tag is right but
whose payload length is wrong is not a malformed number — it is
classified as a wrong-type value, and reported as such.

Values are never clamped or silently corrected. A value outside its
range, of the wrong type, of the wrong payload length, absent, or (for
`BufferCapacity`) not a power of two is rejected outright and the
previously active value is retained — the compiled-in default, or the
last accepted value. The registry write itself succeeds, because the
source does not enforce kernel semantics; the registry therefore shows
what was written while the event log shows what KMES is actually
using. Validation happens twice: once when the change plan is built,
and again in C before the plan is applied, so an out-of-range field
reaching the second gate fails the whole application with `EINVAL`.

Applying a plan is all or nothing, and the capacity swap runs first.
A `BufferCapacity` change that cannot be applied therefore also
prevents `MaxEventSize`, `MaxNestingDepth`, and
`MaxEmitRatePerProcess` from being applied in the same pass, even
though those three are valid and would otherwise take effect
immediately for subsequent syscalls. A `MaxEmitRatePerProcess` change
additionally reconfigures every live rate bucket, clamping any bucket
holding more tokens than the new capacity (§2.4).

A valid `BufferCapacity` different from the current one triggers a
ring buffer swap (§2.5).

## Self-configuration events

KMES reports its own configuration handling through KMES, with origin
class 1. These events are best-effort diagnostics: emission runs
before the configuration is applied and its result is discarded, so a
failed emission neither rolls back a valid application nor activates
an invalid value. Each event's payload is built by a small in-kernel
msgpack writer into a 768-byte buffer; a payload that would exceed it
is silently skipped.

`KMES_SELF_CONFIG_INVALID` reports one missing or invalid value. Its
payload is a msgpack map of exactly nine keys, in order:
`configuration_parent_path` (always `Machine\System\KMES`),
`configuration_name` (the canonical name), `expected_type`,
`expected_min` and `expected_max` (from the key's definition),
`received_kind` (one of `missing`, `wrong_type`, `u32_out_of_range`,
`u64_out_of_range` — a malformed payload length reports
`wrong_type`), `received_type` (the actual registry type code for a
wrong-type value, nil otherwise), `received_value` (the numeric value
for an out-of-range value, nil otherwise), and `retained_value` (the
value KMES continues to use, read before any part of the plan was
applied).

One read reports at most four of these events, which is exactly the
number of configuration keys. A plan that would need more is rejected
before anything is applied, and the entire configuration read is
abandoned.

On a first boot where the KMES key exists but is empty, all four keys
are missing, so the read emits four `KMES_SELF_CONFIG_INVALID` events
and retains all four defaults.

`KMES_BUFFER_SWAP_FAILED` reports a valid `BufferCapacity` change that
could not be applied because replacement rings could not be
allocated. Its payload is a three-key map: `requested_capacity`,
`retained_capacity`, and `errno` — the last carrying the positive
value of `ENOMEM` as an unsigned integer. It is emitted only for
allocation failure; a swap abandoned because migration hit a corrupt
size field produces no event.

## Bootstrap and watching

1. PKM loads. KMES initialises with compiled-in defaults and creates
   per-CPU rings at the default capacity. They are live immediately.
2. The first Machine-hive source registers, making LCS usable. KMES
   enumerates every value under `Machine\System\KMES\`.
3. Valid values are applied. A `BufferCapacity` differing from the
   current one drives a swap; a matching or absent one changes
   nothing.
4. KMES arms a persistent watch on the key through LCS's internal
   watch mechanism — a kernel-internal registration, not a
   userspace fd-based watch. Delivery is filtered to value-set and
   value-deleted notifications on the key itself, so changes in keys
   below `Machine\System\KMES` do not trigger a re-read.
5. If the key does not exist yet, the fallback watch is armed on the
   Machine hive root and fires on subkey creation at any depth. When
   it fires, KMES re-runs the whole bootstrap: discover the key, read
   it, and re-arm the targeted watch. Deleting the key afterwards
   does not re-arm the fallback.
6. On subsequent changes — administrator edit, or a Group Policy push
   at a higher-precedence layer — the watch fires and KMES re-reads,
   validates, and applies or rejects.

## Access to the configuration

The configuration keys inherit the Machine hive root security
descriptor, which grants `KEY_ALL_ACCESS` to SYSTEM and
Administrators and `KEY_READ` to Authenticated Users, so unprivileged processes cannot
change KMES's operational parameters. Enforcement is LCS's, not
KMES's — KMES reads values that LCS has already decided the caller
was entitled to write. Domain policy at a higher-precedence layer
provides defence against a compromised local administrator, since
creating a layer above precedence 0 requires SeTcbPrivilege.

The boot-time capacity is the compiled-in default and is not
separately configurable: making it so would need a channel to deliver
a value to the kernel before the registry exists. Once LCS is
available, capacity changes go through the ordinary swap.
