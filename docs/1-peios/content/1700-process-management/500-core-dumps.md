---
title: Core Dumps
type: concept
description: How Peios captures, stores, and gates access to core dumps — a registry-driven policy, a TCB handler service, and trust-label ACEs that mirror each dump's accessibility to the PIP state of the process it came from.
related:
  - peios/process-management/process-lifecycle
  - peios/pip/understanding-pip
  - peios/access-control/understanding-access-control
---

When a process is terminated by an uncaught fatal signal, the kernel can write a snapshot of its memory, registers, and mappings to a file or pipe — a **core dump**. Dumps are how a programmer reconstructs what was happening at the moment of a crash, what state held what value, what call stack led there. They are also one of the most sensitive things a system can produce: a dump contains arbitrary process memory, which on a real workload includes cached credentials, decrypted data, plaintext from input buffers, cryptographic keys, and environment variables.

Peios treats core dumps as **inherently sensitive**. There is no attempt to enumerate or sanitise what's in a given dump. Instead, dumps are captured and stored under strict access control that mirrors the PIP state of the process they came from, so a dump can never be read by a principal who could not have read the live memory.

## Generation policy

Whether a dump is generated for a given process is determined by a layered policy. The system-wide mode is set in the registry under `\System\CoreDumps\Mode`:

| Value | Name | Behaviour |
|---|---|---|
| 0 | `ForceDisabled` | No dumps generated, regardless of any per-image opt-in. |
| 1 | `Off` (default) | Off by default; per-image manifest can opt in. |
| 2 | `On` | On by default; per-image manifest can opt out. |
| 3 | `ForceEnabled` | Always dumped, per-image opt-out ignored. |

Production Peios systems ship with `Off`. Dev images may flip to `On`. `ForceDisabled` and `ForceEnabled` are operational extremes — the first for high-security environments where dumps must never exist; the second for forensic environments where the operator wants every crash captured.

When the mode is `Off` or `On`, two further sources can override the default:

- The binary's signed manifest may declare `Dumpable: true` or `Dumpable: false`, expressing the binary author's intent.
- The registry override at `\System\CoreDumps\Overrides\<binary-path>\Allow` (REG_DWORD 0/1) lets an operator force a specific binary on or off without touching its manifest, for ad-hoc debugging or operational lockdown.

Resolution at exec time, in order:

1. **PIP-protected source handling** (see below) may force-disable independent of policy.
2. `ForceDisabled` or `ForceEnabled` short-circuits everything else.
3. Registry override at `\System\CoreDumps\Overrides\<binary-path>\Allow`, if present.
4. Manifest `Dumpable` field, if present.
5. Global default (`Off` → no dump, `On` → dump).
6. `PR_SET_DUMPABLE` runtime narrowing — a process can opt itself out further but cannot opt in against policy.

## PIP-protected processes

Core dumps of PIP-protected processes are a potential secret leak: a dump that ends up on disk can be read offline, defeating the protection that prevented direct memory access on the live process. The KACS spec is explicit that *core dumps of PIP-protected processes MUST NOT be readable by non-dominant processes.*

Peios honours this with two complementary mechanisms:

- **`coredumpd` runs at PIP = Isolated.** This is the highest standard PIP type; coredumpd dominates None and Protected sources outright. Dumps from those sources are routed through coredumpd and stored with trust labels that gate read access by PIP dominance.
- **Sources coredumpd cannot dominate** — Isolated processes with `pip_trust` higher than coredumpd's own — fall back to the spec's minimum-viable strategy: the dumpable flag is cleared at exec, and no dump is generated. This is rare and usually applies only to specially-trusted high-tier services.

Together, the common Protected-tier case preserves diagnostics through a properly-protected handler, while the rare top-tier case fails closed.

## How dumps are captured

When the kernel determines a dump should be generated, it pipes the dump data to coredumpd. The kernel's `kernel.core_pattern` sysctl is set by `ksyncd` from the registry to point at `coredumpd`'s pipe handler:

```
|/usr/lib/peios/coredumpd %P %u %s %t %e
```

The kernel runs coredumpd in the crashing process's own context for the dump-generation pass — the dump data flows from kernel memory through the pipe to coredumpd without crossing into a less-protected process. coredumpd writes the dump and a metadata sidecar to its managed storage.

## Storage and access control

Dumps live under `/var/lib/peios/coredumps/`, owned by coredumpd. Each crash produces two files:

| File | Contents |
|---|---|
| `<process_guid>-<timestamp>.dump` | The dump itself — process memory, registers, mappings. |
| `<process_guid>-<timestamp>.meta` | Structured metadata: source process's user SID, PSB at crash time (pip_type, pip_trust, mitigation flags), signal, time, executable path. |

The dump file's security descriptor is constructed at creation by coredumpd to mirror the source process's accessibility:

- **DACL.** Grants `READ` to the source process's user SID. Denies everyone else by default. TCB principals can read via privilege.
- **SACL.** Includes a `SYSTEM_PROCESS_TRUST_LABEL_ACE` whose label SID encodes the source's `pip_type` and `pip_trust` from the recorded PSB. Dumps from PIP-None sources omit the trust label entirely and behave like ordinary files.

Because the SACL trust label is enforced by the same AccessCheck pipeline that gates all other PIP-labelled objects, opening a dump file requires the caller's PSB to dominate the recorded source. A non-dominant process — even one whose user SID matches — is denied at file open. There is no separate retrieval path; the kernel's normal AccessCheck does the gating.

## What gets included

The kernel's `coredump_filter` (per-process bitmap of which mapping types to include — anonymous private, anonymous shared, file-backed private, ELF headers, huge pages, DAX, etc.) is honoured as a **narrowing tool**. A process can choose to dump fewer mapping types than the policy allows; it cannot include more than the policy permits.

`RLIMIT_CORE` is honoured normally as a per-process size cap, additionally clamped by the policy's `MaxSize` value in the registry.

## Retention

`coredumpd` enforces retention rules from `\System\CoreDumps\Retention`:

| Value | Default | Meaning |
|---|---|---|
| `MaxSize` | 1 GB | Total size cap for all stored dumps. Oldest evicted first when exceeded. |
| `MaxAge` | 7 days | Dumps older than this are automatically removed. |
| `MaxPerProcess` | 5 | Per source executable, only the N most recent dumps are kept. |

Eviction emits an audit event so retention activity is not silent.

## Audit

Every dump-generation event emits an audit record:

- The source process's identity (user SID, primary token's authentication ID, PSB)
- The signal that caused termination
- The dump's stored path
- Whether generation succeeded, was suppressed by policy, or was force-disabled by PIP rules

Every dump access also audits — a dump is not an ordinary read. Auditing on access is essential because the dump's contents are exactly the kind of data a compromised process would want to exfiltrate.

## What dumps are not

A few things are deliberately out of scope:

- **No content sanitisation.** Peios does not attempt to identify and remove tokens, credentials, or other secrets from dump contents. Sanitisation is fragile (any miss is a leak) and gives a false sense of safety. Access control over the dump file is the protection.
- **No mediated retrieval API.** Reading a dump is just opening a file; the SD does the work. There is no special syscall, no service to query, no extra permission system. This is by design — the trust label ACE is the right primitive, and reusing the existing AccessCheck pipeline is the simplest correct implementation.
- **No automatic upload.** Dumps stay on the local machine. Any export is a deliberate operator action against managed storage, not a default behaviour.
