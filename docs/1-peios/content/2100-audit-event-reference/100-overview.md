---
title: Audit event reference
type: reference
description: Every audit event emitted by the kernel is a msgpack map with UTF-8 string keys. This page covers the encoding conventions every event shares, the event type names, and the rules consumers should follow.
related:
  - peios/audit-event-reference/event-schemas
  - peios/audit-event-reference/common-records
  - peios/auditing/overview
  - peios/auditing/events-and-transport
---

Audit events in Peios are emitted by the kernel through KMES (the Kernel Message Event Stream) to userspace consumers. Each event is a self-contained record describing what happened — who did it, what was attempted, what the kernel decided, why it fired.

This reference covers the **wire format** for those events. The conceptual model — when each event fires, what audit ACEs are, how the audit pipeline works — is in [Auditing](~peios/auditing/overview). This page is for consumers parsing the events and producers (rare) constructing them.

## Encoding

Every audit event is a **msgpack map** with **UTF-8 string keys**. msgpack is Peios's standard binary serialisation across kernel/userspace boundaries; it's compact, type-safe, and round-trips cleanly.

The map has a stable set of keys per event type, plus an `event_type` discriminator that identifies which type the map represents.

| Key | Value type | Always present? | Meaning |
|---|---|---|---|
| `event_type` | msgpack string | Yes | The event-type name. One of `"access-audit"`, `"continuous-audit"`, `"privilege-use"`, `"logon-session-destroyed"`, etc. |
| `event_time` | msgpack uint | Yes | Timestamp of the event (kernel-internal monotonic units). |

After these, type-specific fields follow. Each event type's specific schema is in [Event schemas](~peios/audit-event-reference/event-schemas).

## Value type conventions

Within event maps:

| Conceptual type | msgpack representation |
|---|---|
| SID | msgpack **bin** containing the binary SID (8–68 bytes). |
| ACE | msgpack **bin** containing the binary ACE (from the matched audit ACE). |
| Access mask | msgpack **uint** (32-bit). |
| Boolean | msgpack **bool**. |
| Privilege name | msgpack **string** (UTF-8 — e.g., "SeBackupPrivilege"). |
| Process ID | msgpack **uint**. |
| Path / name | msgpack **string** (UTF-8). |
| Object context | msgpack **bin** or **nil**. Opaque caller-supplied blob; consumers may treat its contents as service-specific. |

The kernel's conventions are uniform — these representations apply across every event type.

## Forward compatibility

Two rules govern compatibility:

**Consumers should ignore unknown keys.** Future kernel versions may add fields to event maps without changing existing keys. A consumer that processes only the keys it knows about and ignores the rest will continue to work across kernel upgrades.

**Producers should not rely on absent keys.** A field that is "optional" today may become "required" in a future version (rare, but possible). Code that constructs events for testing or replay should be aware of which fields are stable vs. evolving.

The set of fields documented here is stable for the v0.20 line. Additions are possible; field removal or renaming is not (it would be an ABI break, requiring a new major version).

## Event categories

The audit events emitted from the kernel fall into a few categories:

| Category | Event types | Fires at |
|---|---|---|
| **Object access** | `access-audit` | AccessCheck completion (one event per matching audit ACE per access; or via token audit_policy). |
| **Continuous audit** | `continuous-audit` | Per-operation on an open handle whose continuous audit mask matches the operation. |
| **Privilege use** | `privilege-use` | AccessCheck completion when a privilege contributed bits and the token's audit_policy requests it. |
| **Session lifecycle** | `logon-session-destroyed` | When a logon session's last token reference drops. |

Plus diagnostic events the kernel may emit for unusual conditions (corrupt SDs, malformed audit input, etc.). These are documented per-event where they exist.

The four primary event types are covered in detail in [Event schemas](~peios/audit-event-reference/event-schemas). The common sub-records that appear inside several event types (`subject`, `process`, `trigger`) are covered in [Common records](~peios/audit-event-reference/common-records).

## Transport rules

KMES is the transport. Subscribers attach to KMES streams and read events as they come.

A few rules consumers should know:

**Best-effort delivery.** The kernel writes events to KMES; reliable processing is the subscriber's job. A subscriber that falls behind may have events dropped from its buffer.

**Per-subscriber buffers.** Each subscriber has its own KMES buffer. One slow subscriber doesn't affect others; the kernel can keep writing to other subscribers' buffers normally.

**No replay.** Events are produced once. A subscriber that misses an event (subscription gap, buffer overflow) cannot ask for it back.

**No cryptographic authentication.** Events come from the kernel; subscribers trust them by virtue of receiving them via KMES. Cryptographic signing for non-repudiation is a userspace concern, applied after the events leave the kernel.

**Order is per-subscriber, not global.** Events are ordered within a subscriber's stream. Two subscribers reading the same events may see them in slightly different orders if they subscribed at different times or if KMES's per-subscriber buffering introduces small reorderings.

For most audit-pipeline purposes, the best-effort delivery is sufficient — `eventd` (the userspace audit daemon) drains its KMES subscription continuously, persists events to durable storage, and is the source of truth for the deployment's audit log from that point on.

## Where to start

If you want each event type's full field schema — every key, what it means, when it's present, what its values look like — read [Event schemas](~peios/audit-event-reference/event-schemas).

If you want the common sub-record structures (subject, process, trigger) that appear in several event types, read [Common records](~peios/audit-event-reference/common-records).

For the higher-level model of when each event fires, read the relevant pages under [Auditing](~peios/auditing/overview).
