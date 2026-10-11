---
title: Events and transport
type: reference
description: The audit event schemas and the KMES transport that carries them — access checks, handle use, privilege use, CAAP diagnostics and session teardown.
related:
  - peios/auditing/overview
  - peios/auditing/audit-aces
  - peios/auditing/policy-forced-auditing
  - peios/logon-sessions/lifecycle
---

The audit layer is the part of the access check that *generates* events. Once an event has been produced, its further life is the **transport** layer's concern — getting the event from the kernel to whatever userspace consumer is interested. Peios uses **KMES** (Kernel Message Event Stream) for this. The kernel writes events to KMES; userspace daemons subscribe and receive them; eventually they are written to wherever the deployment's audit pipeline wants them.

This page covers the event schemas — what each event type contains — and the transport mechanics at a conceptual level.

## The event types

Six event types come out of the access-check layer and its surroundings:

| Event type | When it fires | Fired by |
|---|---|---|
| `kacs.audit.access.checked` | An SACL audit ACE matched, or a token audit_policy `OBJECT_ACCESS_*` flag forced it | Step 14 and 14b of AccessCheck |
| `kacs.audit.handle.used` | An operation on an open handle matched the handle's continuous audit mask | The kernel enforcement point for the operation (FACS, for file handles, is the only one today) |
| `kacs.audit.privilege.used` | A privilege contributed bits AND the token's audit_policy `PRIVILEGE_USE_*` requested it | Step 13 of AccessCheck |
| `kacs.caap.sacl.skipped` | A CAAP rule's SACL could not be parsed or evaluated, so its audit was skipped | Step 14 of AccessCheck |
| `kacs.caap.staging.diverged` | A staged central access policy decided differently from the effective one | Step 14 of AccessCheck |
| `kacs.session.destroyed` | A logon session lost its last token reference | Session destruction path (independent of access check) |

Each event is a self-describing record. Consumers do not need to know which check produced an event in order to parse it; the event itself carries enough metadata to identify itself and its context. `evman <event-type>` prints the full description of any of them, field by field.

## Event encoding

All audit events are encoded as **msgpack maps with UTF-8 string keys**. msgpack is the binary serialisation format Peios uses across kernel/userspace boundaries; it produces compact records that are quick to parse and round-trip cleanly.

Fields are named by dotted paths, and each segment of a path is one level of nested map: `access.requested` is the key `requested` inside the map under `access`, and `subject.token.sid` is three maps deep. No key ever contains a dot. A value the kernel does not have is **absent** — never nil, an empty string or zero standing in for "none".

SIDs and ACEs appear as **bin** (binary blob) values in the msgpack — the same binary forms used in the kernel. UIDs, LUIDs, timestamps and bitmasks appear as **uint** values; timestamps are realtime nanoseconds. Errors are negative integers. Strings appear as msgpack strings (UTF-8).

Consumers are expected to **ignore unknown keys**. Future kernel versions may add fields to event records without changing the existing ones. A consumer that processes only the fields it knows about and ignores the rest will continue to work across kernel upgrades.

The exact byte-level layout of the SIDs and ACEs is documented in [Wire formats reference](~peios/advanced-peios/wire-formats-reference/overview); this page covers the logical structure.

## The subject

The subject fields appear in every event that involves a calling principal. They identify the token under which the operation ran, and the PIP state in force:

| Field | Type | Meaning |
|---|---|---|
| `subject.token.sid` | bin | The token's user SID. |
| `subject.token.groups` | array of bin | The token's group SIDs. |
| `subject.token.group-attributes` | array of uint | Each group's `SE_GROUP_*` attributes, parallel to `groups`: entry *i* describes group *i*. |
| `subject.token.integrity` | uint | The token's integrity level (one of the well-known integrity RIDs). |
| `subject.token.id` | uint | The token's own LUID. |
| `subject.token.auth-id` | uint | The LUID of the logon session the token belongs to — the key that joins a record to `kacs.session.destroyed`. |
| `subject.token.type` | string | `primary` or `impersonation`. |
| `subject.token.impersonation` | uint | The impersonation level, 0–3. A primary token reports 0, so read `type` first. |
| `subject.token.uid` | uint | The Linux UID the token projects onto. |
| `subject.pip.type` | uint | The PIP type in force for the check. |
| `subject.pip.trust` | uint | The PIP trust level in force for the check. |

To see which groups the check actually matched on the allow side, keep the entries whose attributes have `SE_GROUP_ENABLED` set and `SE_GROUP_USE_FOR_DENY_ONLY` clear.

For events that fire from inside an impersonating thread, the subject reflects the **effective token** — the impersonation token — not the primary. This is what the access check ran against, and it is what should be recorded.

For `kacs.audit.handle.used` events specifically, the subject is the effective token at the moment of the *operation*, not at the moment the handle was opened. A process whose effective token has changed since opening the handle gets the up-to-date subject in each event.

## The emitting process

The same events identify the process the record was written from:

| Field | Type | Meaning |
|---|---|---|
| `emitter.process.pid` | uint | Process ID. |
| `emitter.process.name` | string | Process executable name. |
| `emitter.process.executable` | string | Full path to the executable. |

These fields let a consumer correlate the event with a running (or recently-running) process. The pid is useful in the short term — the process may still exist when the consumer is processing the event. The name and path are useful for human-readable correlation and for long-term records where the pid may have been reused. The durable identifiers — the token and process GUIDs — are in the record's header, not the payload.

## The object

`object.kind` says what sort of thing was checked: `file`, `process`, `token`, `socket`, `ipc`, or a kind a userspace component named. Identity fields sit beneath it — a token check carries `object.token.id` and `object.token.guid`. Not every check can name its object yet: a kernel file check does not carry the file's path, and a process check does not carry the process's pid or GUID. Those fields are absent rather than guessed.

A daemon that checks access to its own objects through `kacs_access_check` names the object with an **audit context**, a msgpack map such as `{kind: "service", service: {name: "jellyfin"}}`. The kernel validates the map — the call fails with `EINVAL` if it is anything else — and copies it into the record as `object.kind` and `object.service.name`. A check made with no audit context has no `object` at all. Those values are the daemon's word rather than something the kernel observed, and so is everything else a `kacs_access_check` caller hands in: the security descriptor, and with it any matched `trigger.ace`, and any PIP type or trust it passes. So every record of a `kacs_access_check` or `kacs_access_check_list` call carries `fields.attestation.userspace = true`, with or without an audit context, and a record of a check the kernel makes itself never does.

## `kacs.audit.access.checked`

The most common event type. Fired by step 14 (SACL audit walk) and step 14b (token audit_policy). Besides the subject, the emitting process and the object:

| Field | Type | Meaning |
|---|---|---|
| `access.requested` | uint | The access mask the caller requested (after generic mapping). |
| `access.granted` | uint | The mask of rights actually granted. |
| `outcome.success` | bool | Whether the access succeeded (granted contains all of requested). |
| `trigger.kind` | string | Either `sacl` (a SACL audit ACE matched) or `policy` (token audit_policy forced it). |
| `trigger.ace` | bin | The matched ACE bytes. Present only when `trigger.kind` is `sacl`. |
| `fields.attestation.userspace` | bool | `true` on every record of a `kacs_access_check` or `kacs_access_check_list` call, whose descriptor, audit context and PIP values are the caller's; absent on a check the kernel makes itself. |

A consumer can use `trigger.kind` to filter: events from SACL ACEs versus events forced by token policy. The `trigger.ace` field includes the bytes of the matched ACE so a consumer can reconstruct what specific rule produced the event.

## `kacs.audit.handle.used`

Fired per-operation on a handle whose continuous audit mask overlaps the operation's required mask. Besides the subject (operation-time effective token, not handle-open token) and the emitting process:

| Field | Type | Meaning |
|---|---|---|
| `object.kind` | string | Always `file` today. |
| `object.file.path` | string | The file's absolute path. |
| `operation.name` | string | The operation name, prefixed with `file.` (e.g. `file.permission`, `file.write`, `file.mmap`). |
| `access.requested` | uint | The required mask for this operation. |
| `access.matched` | uint | The subset of `access.requested` that overlapped the handle's continuous audit mask. |
| `access.granted` | uint | The mask cached on the handle at the time of the operation. |
| `access.audit-mask` | uint | The handle's whole continuous audit mask. |
| `outcome.success` | bool | Whether the operation succeeded. |
| `outcome.reason` | string | Why it failed — `grant-deny`, `append-deny`, `signed-exec` or `unmanaged-sysfs`. Present only on failure. |

The access-mask fields require explanation:

- `access.requested` is what *this operation* asks for. A `read` on a file requires read; an `mmap` requires execute or write depending on mode.
- `access.matched` is the subset of `access.requested` that intersected the handle's continuous audit mask. The event fires because of this overlap; the mask is recorded so consumers know which alarm ACEs were relevant. `access.audit-mask` shows what else on the handle would fire.
- `access.granted` is the cached access mask on the handle from the original open. Operations can only succeed if their required mask is a subset of the cached granted mask, so this field tells consumers what the handle was actually authorised for.

## `kacs.audit.privilege.used`

Fired at step 13 of AccessCheck for each privilege that contributed bits. Besides the subject, the emitting process and the object:

| Field | Type | Meaning |
|---|---|---|
| `privilege.name` | string | The canonical privilege name (e.g. `SeBackupPrivilege`). |
| `privilege.contributed` | uint | The bits the privilege supplied, intersected with what the caller asked for. |
| `privilege.surviving` | uint | The subset of `privilege.contributed` that survived to the final granted mask. |
| `access.requested` | uint | The whole check's requested mask. |
| `access.granted` | uint | The whole check's final granted mask. |
| `outcome.success` | bool | True if `privilege.surviving` is non-empty (the privilege contributed bits that made it through). |
| `fields.attestation.userspace` | bool | As for `kacs.audit.access.checked`. |

The masks tell the full story: what the caller wanted, what the privilege tried to grant, what actually survived. A successful event has a non-empty `privilege.surviving`; a failed event has `privilege.surviving == 0` — the privilege tried to grant bits but they were stripped.

## `kacs.caap.sacl.skipped` and `kacs.caap.staging.diverged`

The two central-access-policy diagnostics carry the subject, the emitting process and the object, and the check's `access.requested`, `access.granted` (the effective grant) and `access.granted-staged` (what the staged policy would have granted).

`kacs.caap.sacl.skipped` also names the rule whose SACL failed: `caap.policy.sid`, `caap.rule.index`, and `caap.phase` (`effective-sacl` or `staged-sacl`), with `outcome.reason` `invalid-caap-sacl` when the SACL would not parse and `caap-sacl-evaluation-error` when it parsed but could not be evaluated. The audit that rule asked for did not happen, and this record is the only sign of it.

`kacs.caap.staging.diverged` carries nothing else. A difference that lies in the audit records rather than the grant leaves the two masks equal; the record's existence is the signal.

## `kacs.session.destroyed`

Fired when a logon session loses its last token reference and is destroyed.

| Field | Type | Meaning |
|---|---|---|
| `object.session.id` | uint | The destroyed session's LUID. |
| `object.session.user.sid` | bin | The user SID the session belonged to. |
| `object.session.logon-type` | string | The session's logon type: `interactive`, `network`, `batch`, `service`, `network-cleartext`, `new-credentials` or `remote-interactive`. |
| `object.session.auth-package` | string | The auth-package name (e.g. "Kerberos", "NTLM", "local"). |
| `object.session.logon-time` | uint | When the session was created, in nanoseconds. |

No subject and no emitting process: the session is identified by its ID, not by any specific principal or process.

The event lets userspace consumers — notably authd — release session-scoped state (Kerberos tickets, cached directory data, per-session credentials).

## KMES transport

The kernel does not directly write audit events to disk, send them over a network, or hand them to a specific userspace process. The kernel writes events to **KMES** — Kernel Message Event Stream — which is a per-subscriber ring buffer with kernel-side production and userspace-side consumption.

Conceptually:

1. The kernel produces an event (e.g. an audit fires during step 14).
2. The kernel writes the event into each subscriber's KMES buffer.
3. Userspace consumers read from their KMES buffers when they are ready.
4. Once a buffer is drained, the kernel can continue producing into it.

The buffers are per-subscriber. A subscriber that falls behind has its own buffer fill up; eventually KMES applies flow control to that buffer (typically dropping the oldest events). The kernel's production of events to other subscribers is unaffected.

The audit subsystem typically has at least one subscriber: **`eventd`**, the userspace audit daemon. `eventd` subscribes to the audit event types, reads them from KMES, and writes them to wherever the deployment's audit pipeline goes (a local file, a remote syslog, a SIEM collector). Other subscribers — debugging tools, real-time monitors — can also exist.

The exact KMES protocol, buffer sizes, flow-control mechanics, and reliability guarantees are outside the scope of this auditing topic; they are defined in [PSPK §2](~peios/kmes-event-stream/scope), the kernel-boundary protocol standard in which KMES is the core abstraction. For auditing purposes, what matters is:

- Events are not retained by the kernel beyond writing them to KMES.
- A subscriber that falls behind may lose events.
- Reliable persistence is the job of whoever drains the KMES buffer, not the kernel.

## What consumers should look at

For someone writing or operating an audit consumer:

- **Filter by event type.** Most consumers care about specific types (just `kacs.audit.access.checked` for compliance, just `kacs.audit.privilege.used` for privilege monitoring, etc.). The dotted names nest, so `kacs.audit` selects the whole audit trail. Filtering early reduces processing volume.
- **Correlate by subject + object.** A consumer that wants to track "everything user X did to object Y" should index events by `subject.token.sid` and the `object.*` fields; `subject.token.auth-id` gathers everything from one sign-on.
- **Use the trigger field to distinguish event sources.** A `kacs.audit.access.checked` with `trigger.kind` `policy` was forced by token audit policy; one with `sacl` came from a specific ACE. The distinction matters for some compliance scenarios.
- **Do not read asserted values as observed.** A record with `fields.attestation.userspace` carries a userspace component's claim, about its object and the descriptor it checked against, which the kernel copied but did not verify.
- **Be tolerant of new fields.** Future kernel versions may add fields to event records. Ignoring unknown keys is the rule; rejecting events with unfamiliar fields is a bug.
- **Plan for event loss.** A KMES subscriber that falls behind loses events. Consumers that need lossless audit must implement their own persistence layer above KMES and handle backpressure appropriately.

## What the audit transport does not provide

A few clarifications:

- **No reliable delivery to the kernel's edge.** Events written to KMES are best-effort; a crashing subscriber loses its buffer. The kernel does not block access checks on subscriber readiness.
- **No replay.** A consumer that joins late, or one that loses its connection, cannot ask for old events. The events are produced once; missing them means missing them.
- **No event correlation across boots.** Each boot starts fresh. Audit logs that span reboots are assembled by userspace persistence (eventd writing to disk, log aggregators collecting across systems).
- **No authentication of events at the consumer.** Events are produced by the kernel and received by KMES subscribers. There is no signature on events; the trust model is "the kernel said this, so it is true". A subscriber that needs cryptographic non-repudiation of events would need to add a signing layer in userspace.

The model is built for performance and simplicity over absolute guarantees. For deployments that need stronger properties, the userspace audit pipeline is where additional layers belong — not in the kernel-to-KMES boundary.

## See also

- [Auditing](~peios/auditing/overview) — the model these events come from.
- [Audit ACEs](~peios/auditing/audit-aces) — the SACL mechanisms behind access-check and handle-use events.
- [Policy-forced auditing](~peios/auditing/policy-forced-auditing) — the token policy behind privilege-use and forced object-access events.
- [Wire formats reference](~peios/advanced-peios/wire-formats-reference/overview) — byte-level encoding of the SIDs and ACEs carried in events.
