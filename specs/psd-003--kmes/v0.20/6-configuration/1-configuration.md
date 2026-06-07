---
title: Self-Configuration
---

KMES reads its operational parameters from the registry under `Machine\System\KMES\`. Compiled-in defaults are used at boot. When LCS becomes available, KMES reads the configuration keys, validates them, and applies valid values. A persistent watch on the configuration subtree ensures ongoing changes are picked up for the lifetime of operation.

## Configuration keys

All keys live under `Machine\System\KMES\`. Each has a defined type, compiled-in default, and valid range. KMES ignores unknown keys in this subtree.

KMES configuration value names are matched using the LCS value-name comparison rules: Unicode Simple Case Folding, case-preserving, and case-insensitive. The canonical key names in the table below identify the KMES-controlled setting and are used in KMES self-configuration audit payloads. Registry entries whose folded value name does not match one of these canonical names are unknown keys and are ignored.

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| BufferCapacity | REG_QWORD | 4194304 | 65536--268435456 | Per-CPU ring buffer capacity in bytes. MUST be a power of two. Values that are not powers of two are treated as invalid. Default is 4 MB. Maximum is 256 MB. |
| MaxEventSize | REG_DWORD | 65536 | 1024--4194304 | Maximum permitted total event size (header + payload) in bytes for events emitted via the `kmes_emit` and `kmes_emit_batch` syscalls. Does not apply to kernel emitters, which are subject only to the 50% structural limit. Default is 64 KB. Maximum is 4 MB. |
| MaxNestingDepth | REG_DWORD | 32 | 4--256 | Maximum permitted msgpack nesting depth for payloads emitted via the `kmes_emit` and `kmes_emit_batch` syscalls. Payloads exceeding this depth are rejected. Does not apply to kernel emitters. |
| MaxEmitRatePerProcess | REG_DWORD | 10000 | 100--1000000 | Maximum events per second that a single process may emit via the `kmes_emit` and `kmes_emit_batch` syscalls. Implemented as a token bucket: refill rate equals this value, burst capacity equals this value. Processes holding SeTcbPrivilege are exempt. Prevents a compromised application from flooding the ring buffer and overwriting legitimate kernel events. Does not apply to kernel emitters. Rate state is per-process, not per-principal -- per-SID rate limiting would unfairly penalise unrelated services sharing a SID (e.g., LocalService). A process that forks to reset its rate limit is bounded by RLIMIT_NPROC. For batch emission, only events actually emitted are charged, not the full requested count. |

## Validation

When KMES reads a configuration value, it validates against the defined type, payload length, range, and constraints. `REG_DWORD` KMES values MUST contain exactly four little-endian payload bytes. `REG_QWORD` KMES values MUST contain exactly eight little-endian payload bytes. A value whose registry type tag is `REG_DWORD` or `REG_QWORD` but whose payload length is wrong for that type is invalid and is treated as a wrong-type value for retention and self-configuration audit purposes.

- **Valid value:** Applied to the in-memory configuration. For MaxEventSize and MaxNestingDepth, the new value takes effect for subsequent syscalls. For BufferCapacity, KMES triggers a ring buffer swap -- creating new per-CPU ring buffers at the configured size, copying surviving events from the old buffers, incrementing the generation counter, and discarding the old buffers. The swap protocol is defined in §5.1.9.4.

- **Invalid value** (out of range, wrong type, malformed payload length, not a power of two for BufferCapacity, missing): Ignored. KMES retains the previously active value (compiled-in default or last known-good). An event is emitted via KMES itself identifying the key, the invalid value class, and the value being retained.

Values are never clamped or silently corrected. The write to the registry succeeds (the source does not enforce kernel semantics), but KMES refuses to use it. The registry shows what was written; the event log shows what KMES is actually using.

## Self-configuration events

KMES emits self-configuration events with origin class `KMES`. These events are best-effort diagnostics. Failure to emit a self-configuration event MUST NOT roll back a valid configuration application and MUST NOT make an invalid configuration value active.

### `KMES_SELF_CONFIG_INVALID`

KMES emits `KMES_SELF_CONFIG_INVALID` when a defined configuration value is missing or invalid during a self-configuration read. The payload is a msgpack map with exactly these keys:

| Key | Type | Description |
|---|---|---|
| `configuration_parent_path` | string | Canonical parent path, `Machine\System\KMES`. |
| `configuration_name` | string | Canonical KMES configuration key name from the table above. |
| `expected_type` | unsigned integer | Expected LCS registry type code. |
| `expected_min` | unsigned integer | Minimum accepted numeric value for the key. |
| `expected_max` | unsigned integer | Maximum accepted numeric value for the key. |
| `received_kind` | string | One of `missing`, `wrong_type`, `u32_out_of_range`, or `u64_out_of_range`. Malformed `REG_DWORD` or `REG_QWORD` payload lengths use `wrong_type`. |
| `received_type` | unsigned integer or nil | Actual registry type code for `wrong_type`; nil for `missing` and out-of-range values. |
| `received_value` | unsigned integer or nil | Numeric value for out-of-range values; nil for `missing` and `wrong_type`. |
| `retained_value` | unsigned integer | Previously active value retained by KMES. |

### `KMES_BUFFER_SWAP_FAILED`

KMES emits `KMES_BUFFER_SWAP_FAILED` when a valid `BufferCapacity` configuration change cannot be applied because KMES cannot allocate replacement ring buffers. The payload is a msgpack map with exactly these keys:

| Key | Type | Description |
|---|---|---|
| `requested_capacity` | unsigned integer | Valid requested BufferCapacity value that triggered the swap attempt. |
| `retained_capacity` | unsigned integer | Active BufferCapacity value retained by KMES. |
| `errno` | signed integer | Kernel errno for the failed swap attempt. |

## Bootstrap sequence

1. PKM loads. KMES initialises with compiled-in defaults and creates per-CPU ring buffers at the compiled-in default BufferCapacity. These are ordinary consumer-facing KMES ring buffers and receive events immediately.

2. LCS becomes available (first source registers). KMES reads all keys under `Machine\System\KMES\`.

3. If keys exist and are valid, KMES applies them. If BufferCapacity differs from the compiled-in default, KMES performs a normal ring-buffer swap: it creates new per-CPU ring buffers at the configured size, copies surviving events from the existing buffers into them, increments generation, and switches writers to the new buffers. If BufferCapacity matches the default (or the key does not exist), no capacity change is needed and the existing buffers remain in place.

4. KMES arms a persistent subtree watch on `Machine\System\KMES\` via LCS's internal watch mechanism. This is a kernel-internal registration, not a userspace fd-based watch.

5. If `Machine\System\KMES\` does not exist (first boot, empty database), KMES arms a watch on a parent key to detect when the subtree is created. When the key appears, KMES reads and validates its contents and re-arms a targeted watch.

6. On subsequent changes (administrator modification, Group Policy push at a higher-precedence layer), the watch fires, KMES re-reads the changed key, validates, and applies or rejects.

At no point does KMES enter a "waiting for configuration" state. Compiled-in defaults are always sufficient for operation.

## Security

KMES configuration keys live under `Machine\System\KMES\`, which inherits the Machine hive root SD (SYSTEM and Administrators: KEY_ALL_ACCESS, Authenticated Users: KEY_READ). Unprivileged processes cannot modify operational parameters.

Domain policy enforcement via Group Policy at a higher-precedence layer provides defence against compromised local administrators -- SeTcbPrivilege is required for layer creation at precedence > 0.

KMES configuration keys are candidates for Superlock protection (a future registry feature that prevents modification outside of Safe or Recovery mode). Event system configuration is critical enough that runtime modification by even a privileged administrator warrants additional gating.

## Boot-time initial capacity

The capacity of the initial boot-time ring buffers is the compiled-in default BufferCapacity. It is not independently configurable before LCS is available. Making the pre-LCS capacity separately configurable would require a mechanism to deliver the value to the kernel before the registry exists, which adds complexity for negligible benefit. Once LCS is available, BufferCapacity changes are applied through the normal generation-bumping ring-buffer swap protocol.
