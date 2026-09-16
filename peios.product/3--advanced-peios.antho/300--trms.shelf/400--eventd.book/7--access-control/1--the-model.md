---
title: The Model
description: eventd enforces access on the read path only, through KACS descriptors, and decides nothing itself — caller identity, rights and timing.
---

eventd enforces access on the **read path only**, using KACS Security
Descriptors and the KACS AccessCheck API. Every query is evaluated
against descriptors that determine which records — and which fields
within a record — the caller may see, and everything else is filtered
out silently (PSPU §3.28).

## eventd decides nothing itself [*access.eventd-delegates-every-decision-to-kacs-accesscheck]

eventd implements no access check logic of its own. Every decision is
delegated to `kacs_access_check` and `kacs_access_check_list`, which run
the full KACS AccessCheck pipeline: integrity checks, restricted token
evaluation, confinement, conditional ACE evaluation, and the SACL audit
walk.

What eventd contributes is the three things AccessCheck needs and cannot
know — which descriptor applies (§7.2), which object type list describes
the record (§7.3), and what the caller's token is (§7.4) — and then it
acts on the verdicts.

The alternative would be reimplementing an access check algorithm that
already exists, in a daemon that would then have to be kept in agreement
with it forever.

## Enforcement is at query time [*access.access-is-enforced-at-query-time]

All events, logs and metrics are stored regardless of who will ever be
allowed to read them, and two callers querying the same store see
different results.
[*access.every-record-is-stored-regardless-of-who-may-read-it]

Three reasons make this the only workable arrangement:

- **Audit integrity.** An audit event has to be stored whether or not
  anyone can currently read it. Filtering at storage time would let a
  descriptor decide what gets recorded, which is the one thing an audit
  store must not permit.
- **Descriptors change.** An administrator can grant or revoke access
  retroactively, and only query-time evaluation makes that meaningful.
  [*access.a-grant-or-revocation-applies-retroactively-to-stored-records]
- **Callers differ.** Several principals with different access levels
  query the same store, and there is one copy of the data.

## Caller identity

When a client connects to the query socket, eventd obtains its token by
reading the peer-token socket option (`getsockopt(SOL_KACS,
KACS_SO_PEER_TOKEN)`) on the connected descriptor.
[*access.the-caller-token-is-read-from-the-peer-token-socket-option] The token
represents the peer's identity as captured **at connection time**.
[*access.the-caller-token-is-captured-at-connection-time]

If the call fails, eventd denies the query entirely.
[*access.a-failed-peer-token-read-denies-the-query] It has no fallback
identification and no anonymous mode.
[*access.there-is-no-fallback-identification-or-anonymous-mode]

The snapshot property matters most for streaming queries, which may run
indefinitely: a client whose group memberships change, or whose access
is revoked, continues to be evaluated against the token it connected
with until it disconnects (§7.5).

## Rights

| Right | Bit | Value | Meaning |
|---|---|---|---|
| `EVENTD_READ` | 0 | 0x0001 | Read records matching the pattern. [*access.eventd-read-is-bit-0-value-0x0001] |
| `EVENTD_CLEAR` | 1 | 0x0002 | Delete records matching the pattern. [*access.eventd-clear-is-bit-1-value-0x0002] |
| `EVENTD_ADMINISTER` | 2 | 0x0004 | Change eventd's own policy — the `INDEX` command (§7.2). [*access.eventd-administer-is-bit-2-value-0x0004] |

The generic mapping passed to AccessCheck is in §B.

`EVENTD_ADMINISTER` is distinct from `EVENTD_READ` deliberately.
[*access.eventd-read-alone-does-not-grant-eventd-administer]
Accelerating a field costs write throughput on every record thereafter,
so `INDEX` is a way for a caller to degrade the system for everybody,
and a caller permitted only to read has not been permitted to do that
(PSPU §3.23).

> [!NOTE]
> `EVENTD_CLEAR` is defined and nothing yet uses it: no operation deletes
> records on a caller's behalf, and retention deletes on nobody's behalf
> (§3.6). [*access.no-operation-uses-eventd-clear] It is reserved for
> administrative deletion. The consequence
> worth knowing is that a descriptor written today with `GENERIC_WRITE`
> already grants it, and will start granting a real capability the moment
> one exists. [*access.generic-write-already-grants-eventd-clear]

## What is not controlled here

**Event emission** is KMES's: `kmes_emit` and `kmes_emit_batch` require
SeAuditPrivilege, and eventd is not involved.

**Log and metric ingestion** has no per-record control at all. The
Security Descriptor on each ingestion socket is the entirety of it
(§7.6).
