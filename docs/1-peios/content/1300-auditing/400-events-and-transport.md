---
title: Events and transport
type: concept
description: Audit events are msgpack maps with UTF-8 keys, emitted by the kernel through KMES to userspace consumers. This page covers the event schemas — access-audit, continuous-audit, privilege-use, logon-session-destroyed — and how the transport pipeline works.
related:
  - peios/auditing/overview
  - peios/auditing/audit-aces
  - peios/auditing/policy-forced-auditing
  - peios/logon-sessions/lifecycle
---

The audit layer is the part of the access check that *generates* events. Once an event has been produced, its further life is the **transport** layer's concern — getting the event from the kernel to whatever userspace consumer is interested. Peios uses **KMES** (Kernel Message Event Stream) for this. The kernel writes events to KMES; userspace daemons subscribe and receive them; eventually they are written to wherever the deployment's audit pipeline wants them.

This page covers the event schemas — what each event type contains — and the transport mechanics at a conceptual level.

## The event types

Four event types come out of the access-check layer:

| Event type | When it fires | Fired by |
|---|---|---|
| `access-audit` | An SACL audit ACE matched, or a token audit_policy `OBJECT_ACCESS_*` flag forced it | Step 14 and 14b of AccessCheck |
| `continuous-audit` | An operation on an open handle matched the handle's continuous audit mask | The enforcement point for the operation (FACS, registryd, etc.) |
| `privilege-use` | A privilege contributed bits AND the token's audit_policy `PRIVILEGE_USE_*` requested it | Step 13 of AccessCheck |
| `logon-session-destroyed` | A logon session lost its last token reference | Session destruction path (independent of access check) |

Each event is a self-describing record. Consumers do not need to know which check produced an event in order to parse it; the event itself carries enough metadata to identify itself and its context.

## Event encoding

All audit events are encoded as **msgpack maps with UTF-8 string keys**. msgpack is the binary serialisation format Peios uses across kernel/userspace boundaries; it produces compact records that are quick to parse and round-trip cleanly.

SIDs and ACEs appear as **bin** (binary blob) values in the msgpack — the same binary forms used in the kernel. UIDs, timestamps, and bitmasks appear as **uint** values. Strings appear as msgpack strings (UTF-8).

Consumers are expected to **ignore unknown keys**. Future kernel versions may add fields to event records without changing the existing ones. A consumer that processes only the fields it knows about and ignores the rest will continue to work across kernel upgrades.

The msgpack format and the key conventions are stable across the v0.20 line. The exact byte-level layout is documented in [Wire formats reference](~peios/wire-formats-reference/overview); this page covers the logical structure.

## The subject record

A subject record appears in every event that involves a calling principal. It identifies the token under which the operation ran:

| Field | Type | Meaning |
|---|---|---|
| `user_sid` | bin | The token's user SID. |
| `group_sids` | array of bin | The token's group SIDs (with attributes, in the same SID_AND_ATTRIBUTES form the token holds). |
| `integrity_level` | uint | The token's integrity level (one of the well-known integrity RIDs). |
| `pip_type` | uint | The PIP type of the calling process. |
| `pip_trust` | uint | The PIP trust level of the calling process. |

For events that fire from inside an impersonating thread, the subject reflects the **effective token** — the impersonation token — not the primary. This is what the access check ran against, and it is what should be recorded.

For continuous-audit events specifically, the subject is the effective token at the moment of the *operation*, not at the moment the handle was opened. A process whose effective token has changed since opening the handle gets the up-to-date subject in each continuous-audit event.

## The process record

A process record identifies the kernel-level context the event came from:

| Field | Type | Meaning |
|---|---|---|
| `pid` | uint | Process ID. |
| `name` | string | Process executable name. |
| `executable_path` | string | Full path to the executable. |

These fields let a consumer correlate the event with a running (or recently-running) process. The pid is useful in the short term — the process may still exist when the consumer is processing the event. The name and path are useful for human-readable correlation and for long-term records where the pid may have been reused.

## `access-audit` event schema

The most common event type. Fired by step 14 (SACL audit walk) and step 14b (token audit_policy).

| Field | Type | Meaning |
|---|---|---|
| `subject` | map | The subject record. |
| `object_context` | bin or nil | Caller-supplied opaque object identifier. nil if not provided. |
| `requested_access` | uint | The access mask the caller requested (after generic mapping). |
| `granted_access` | uint | The mask of rights actually granted. |
| `success` | bool | Whether the access succeeded (granted contains all of requested). |
| `trigger` | map | Trigger record — see below. |
| `process` | map | The process record. |

The `trigger` map identifies why this event fired:

| Field | Type | Meaning |
|---|---|---|
| `kind` | string | Either "sacl" (a SACL audit ACE matched) or "policy" (token audit_policy forced it). |
| `ace` | bin or nil | For "sacl" triggers, the matched ACE bytes. For "policy" triggers, nil. |

A consumer can use `trigger.kind` to filter: events from SACL ACEs versus events forced by token policy. The `ace` field for SACL triggers includes the bytes of the matched ACE so a consumer can reconstruct what specific rule produced the event.

## `continuous-audit` event schema

Fired per-operation on a handle whose continuous audit mask overlaps the operation's required mask.

| Field | Type | Meaning |
|---|---|---|
| `subject` | map | The subject record (operation-time effective token, not handle-open token). |
| `object_context` | bin or nil | Object identifier, if retained by the enforcement point. |
| `operation` | string | The operation name. For FACS operations, prefixed with `file.` (e.g. `file.read`, `file.write`). |
| `requested_access` | uint | The required mask for this operation. |
| `matched_access` | uint | The subset of required_access that overlapped the handle's continuous audit mask. |
| `granted_access` | uint | The mask cached on the handle at the time of the operation. |
| `success` | bool | Whether the operation succeeded. |
| `process` | map | The process record. |

The two access-mask fields require explanation:

- `requested_access` is what *this operation* asks for. A `read` on a file requires read; an `mmap` requires execute or write depending on mode.
- `matched_access` is the subset of `requested_access` that intersected the handle's continuous audit mask. The event fires because of this overlap; the mask is recorded so consumers know which alarm ACEs were relevant.
- `granted_access` is the cached access mask on the handle from the original open. Operations can only succeed if their required mask is a subset of the cached granted mask, so this field tells consumers what the handle was actually authorised for.

## `privilege-use` event schema

Fired at step 13 of AccessCheck for each privilege that contributed bits.

| Field | Type | Meaning |
|---|---|---|
| `subject` | map | The subject record. |
| `object_context` | bin or nil | Object identifier (the same one the access check was for). |
| `privilege` | string | The canonical privilege name (e.g. `SeBackupPrivilege`). |
| `requested_access` | uint | The bits the caller requested that this privilege might address. |
| `granted_access` | uint | The bits the privilege actually contributed. |
| `surviving_access` | uint | The subset of `granted_access` that survived to the final granted mask. |
| `success` | bool | True if `surviving_access` is non-empty (the privilege contributed bits that made it through). |
| `process` | map | The process record. |

The three access masks tell the full story: what the caller wanted, what the privilege tried to grant, what actually survived. A successful privilege-use event has `granted_access == surviving_access` (or close to it — the surviving subset is what mattered). A failed event has `surviving_access == 0` — the privilege tried to grant bits but they were stripped.

## `logon-session-destroyed` event schema

Fired when a logon session loses its last token reference and is destroyed.

| Field | Type | Meaning |
|---|---|---|
| `session_id` | uint | The destroyed session's LUID. |
| `user_sid` | bin | The user SID the session belonged to. |
| `logon_type` | uint | The session's logon type. |
| `auth_package` | string | The auth-package name (e.g. "Kerberos", "NTLM", "local"). |
| `created_at` | uint | The session's creation timestamp. |

No subject record (the subject *was* this session). No process record (the session is identified by its ID, not by any specific process).

The event lets userspace consumers — notably authd — release session-scoped state (Kerberos tickets, cached directory data, per-session credentials).

## KMES transport

The kernel does not directly write audit events to disk, send them over a network, or hand them to a specific userspace process. The kernel writes events to **KMES** — Kernel Message Event Stream — which is a per-subscriber ring buffer with kernel-side production and userspace-side consumption.

Conceptually:

1. The kernel produces an event (e.g. an audit fires during step 14).
2. The kernel writes the event into each subscriber's KMES buffer.
3. Userspace consumers read from their KMES buffers when they are ready.
4. Once a buffer is drained, the kernel can continue producing into it.

The buffers are per-subscriber. A subscriber that falls behind has its own buffer fill up; eventually KMES applies flow control to that buffer (typically dropping the oldest events). The kernel's production of events to other subscribers is unaffected.

The audit subsystem typically has at least one subscriber: **`eventd`**, the userspace audit-daemon. `eventd` subscribes to the audit event types, reads them from KMES, and writes them to wherever the deployment's audit pipeline goes (a local file, a remote syslog, a SIEM collector). Other subscribers — debugging tools, real-time monitors — can also exist.

The exact KMES protocol, buffer sizes, flow-control mechanics, and reliability guarantees are outside the scope of this auditing topic; they are defined in the [observability documentation](~peios/observability/overview) where KMES is the core abstraction. For auditing purposes, what matters is:

- Events are not retained by the kernel beyond writing them to KMES.
- A subscriber that falls behind may lose events.
- Reliable persistence is the job of whoever drains the KMES buffer, not the kernel.

## What consumers should look at

For someone writing or operating an audit consumer:

- **Filter by event type.** Most consumers care about specific types (just `access-audit` for compliance, just `privilege-use` for privilege monitoring, etc.). Filtering early reduces processing volume.
- **Correlate by subject + object_context.** A consumer that wants to track "everything user X did to object Y" should index events by these two fields.
- **Use the trigger field to distinguish event sources.** An `access-audit` with trigger "policy" was forced by token audit policy; one with trigger "sacl" came from a specific ACE. The distinction matters for some compliance scenarios.
- **Be tolerant of new fields.** Future kernel versions may add fields to event records. Ignoring unknown keys is the rule; rejecting events with unfamiliar fields is a bug.
- **Plan for event loss.** A KMES subscriber that falls behind loses events. Consumers that need lossless audit must implement their own persistence layer above KMES and handle backpressure appropriately.

## What the audit transport does not provide

A few clarifications:

- **No reliable delivery to the kernel's edge.** Events written to KMES are best-effort; a crashing subscriber loses its buffer. The kernel does not block access checks on subscriber readiness.
- **No replay.** A consumer that joins late, or one that loses its connection, cannot ask for old events. The events are produced once; missing them means missing them.
- **No event correlation across boots.** Each boot starts fresh. Audit logs that span reboots are assembled by userspace persistence (eventd writing to disk, log aggregators collecting across systems).
- **No authentication of events at the consumer.** Events are produced by the kernel and received by KMES subscribers. There is no signature on events; the trust model is "the kernel said this, so it is true". A subscriber that needs cryptographic non-repudiation of events would need to add a signing layer in userspace.

The model is built for performance and simplicity over absolute guarantees. For deployments that need stronger properties, the userspace audit pipeline is where additional layers belong — not in the kernel-to-KMES boundary.
