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
sufficient, and if LCS never appears KMES runs on them indefinitely. [*config.defaults-carry-until-lcs]

## Reading and validating

Value names are matched with LCS's value-name comparison rules —
Unicode Simple Case Folding, case-preserving and case-insensitive.
Names in the subtree that do not fold to one of the four canonical
names are unknown keys: they are counted and ignored. [*config.names-case-folded-unknown-ignored]

A `REG_DWORD` value carries exactly four little-endian payload bytes
and a `REG_QWORD` exactly eight. A value whose type tag is right but
whose payload length is wrong is not a malformed number — it is
classified as a wrong-type value, and reported as such. [*config.wrong-length-is-wrong-type]

Values are never clamped or silently corrected. A value outside its
range, of the wrong type, of the wrong payload length, absent, or (for
`BufferCapacity`) not a power of two is rejected outright and the
previously active value is retained — the compiled-in default, or the
last accepted value. The registry write itself succeeds, because the
source does not enforce kernel semantics; the registry therefore shows
what was written while the event log shows what KMES is actually
using. [*config.invalid-rejected-not-clamped] Validation happens twice: once when the change plan is built,
and again in C before the plan is applied, so an out-of-range field
reaching the second gate fails the whole application with `EINVAL`. [*config.validated-twice]

The capacity swap runs first, and a `BufferCapacity` change that
cannot be applied rolls back the capacity and nothing else:
`MaxEventSize`, `MaxNestingDepth`, and `MaxEmitRatePerProcess` still
commit in the same pass, against the capacity that is actually live,
so the stored configuration describes the running system rather than
the requested one. The situation that makes a swap fail — memory
pressure — is exactly the one in which an administrator raising
`MaxEventSize` and `BufferCapacity` together needs the `MaxEventSize`
change to survive. [*config.swap-failure-rolls-back-capacity-only] A
`MaxEmitRatePerProcess` change additionally reconfigures every live
rate bucket, clamping any bucket holding more tokens than the new
capacity (§2.4).

A valid `BufferCapacity` different from the current one triggers a
ring buffer swap (§2.5). [*config.capacity-change-swaps]

## Self-configuration events [*config.self-events-origin-kmes]

KMES reports its own configuration handling through KMES, with origin
class 1. These events are best-effort diagnostics: emission runs
before the configuration is applied and its result is discarded, so a
failed emission neither rolls back a valid application nor activates
an invalid value. Each event's payload is built by a small in-kernel
msgpack writer into a 768-byte buffer; a payload that would exceed it
is silently skipped. [*config.self-events-best-effort]

`kmes.config.value.rejected` reports one missing or invalid value. Its
payload follows the event-field rules of PGSS §6: each dotted field
path is a nested msgpack map, one per segment, and a field that does
not apply is absent rather than nil. Every field lives under a single
top-level `config` map of five keys, in order:

- `config.key.path` — always `Machine\System\KMES`.
- `config.name` — the canonical value name.
- `config.expected.type`, `config.expected.min` and
  `config.expected.max` — the registry type code and range from the
  key's definition.
- `config.received.kind` — one of `missing`, `wrong-type` or
  `out-of-range`. A malformed payload length reports `wrong-type`. A
  `REG_DWORD` and a `REG_QWORD` value out of range both report
  `out-of-range`, since `config.expected.type` already gives the
  width. `config.received.type` (the actual registry type code) is
  present exactly when the kind is `wrong-type`, and
  `config.received.value` (the number received) exactly when it is
  `out-of-range`. A missing value carries the kind alone.
- `config.value` — the value KMES continues to use, read before any
  part of the plan was applied. [*config.invalid-event-nine-keys]

One read reports at most four of these events, which is exactly the
number of configuration keys. A plan that would need more is rejected
before anything is applied, and the entire configuration read is
abandoned. [*config.at-most-four-reports]

On a first boot where the KMES key exists but is empty, all four keys
are missing, so the read emits four `kmes.config.value.rejected`
events and retains all four defaults. [*config.empty-key-emits-four]

`kmes.buffer.swap.failed` reports a valid `BufferCapacity` change that
could not be applied. Its payload is two maps: `buffer`, holding
`buffer.capacity-requested` (the capacity asked for) and
`buffer.capacity` (the capacity kept), and `outcome`, holding
`outcome.errno` as a negative signed integer — `-ENOMEM` when the
replacement rings could not be allocated, which is the usual case.
The swap is system-wide, so no CPU or ring is named. [*config.swap-failed-event]
Every failure is reported, not only allocation: a swap abandoned
because migration met a corrupt size field reports `-EIO`, and one the
kernel could not quiesce the CPUs for reports what `stop_machine`
returned. [*config.swap-failed-every-errno]

`kmes.config.applied` records a read of `Machine\System\KMES` that
reached the commit, after the rejection reports and the commit
itself. Its payload is three maps: `config`, holding `config.key.path`
and `config.counts` with the four counts `applied`, `retained-missing`,
`retained-invalid` and `ignored-unknown`; `buffer`, holding
`buffer.capacity`; and `emission`, holding `emission.rate-limit`. The
capacity and rate are read back after the commit, so they are what is
in force rather than what the plan asked for. [*config.applied-event]
A read whose capacity swap failed still reaches the commit — the other
three settings commit without it — so it is recorded as applied too,
with the capacity kept, beside the `kmes.buffer.swap.failed` that says
why. [*config.applied-after-failed-swap] `MaxEventSize` and
`MaxNestingDepth` in force are not in the record: the catalogue has no
field for either yet.

`kmes.config.refresh.failed` records a re-read, after the watch saw a
change, that failed: the source did not answer, answered with
something malformed, or the plan was refused (more than four rejection
reports, or a configuration the second gate rejects). Its payload is
`config`, holding `config.key.path`, and `outcome`, holding
`outcome.errno`. The configuration in force stays as it was. The
record is `essential`: the registry and the running kernel disagree
until the next change, and it is the only sign. A failed capacity swap
is not a failed read and does not produce one. [*config.refresh-failed-event]
A read that fails during the bootstrap refresh is not recorded this
way: it fails that refresh, which is traced and leaves the machine-root
fallback armed to try again (LCS §5.10.4). The emission policy reports
a failed walk of `Machine\Generic\Events` with the same record (§2.8).

## Bootstrap and watching [*config.bootstrap-sequence]

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
   below `Machine\System\KMES` do not trigger a re-read. [*config.watch-filtered-to-key]
5. If the key does not exist yet, the fallback watch is armed on the
   Machine hive root and fires on subkey creation at any depth. When
   it fires, KMES re-runs the whole bootstrap: discover the key, read
   it, and re-arm the targeted watch. Deleting the key afterwards
   does not re-arm the fallback. [*config.fallback-watch-on-hive-root]
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
available, capacity changes go through the ordinary swap. [*config.boot-capacity-compiled-in]
