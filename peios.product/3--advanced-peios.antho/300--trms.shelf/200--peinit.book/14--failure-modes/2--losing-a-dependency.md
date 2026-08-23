---
title: Losing a Dependency
description: What breaks when authd, eventd or JFS is unavailable, and what a bound dependency that never becomes satisfying does.
---

## authd

Without authd, no non-SYSTEM service can obtain a token, so every such
start fails with `ParentSetupFailure`. Platform services are unaffected,
since they never take that path.

authd is Critical, so its own failure eventually reboots the system
rather than leaving it in a state where no user-facing service can
start.

## eventd

peinit supervises eventd like anything else, and eventd is Critical.
While it is down, peinit re-enables the pre-eventd buffer (§11.2) and
keeps collecting output; when eventd returns the handoff repeats.

There is a log gap bounded by the buffer size. There is **no** event gap
— audit events land in the KMES ring buffer regardless of eventd's
state, and eventd resumes from the last persisted sequence.

## JFS

The device may not exist. Phase 1 treats a failure to open `/dev/jfs` as
a warning and continues, and the boot is unaffected. Nothing else in
peinit depends on it.

## A bound dependency

A service that `BindsTo` something is stopped when that something stops,
with cause `BindsToPropagation`, and restarted when it returns, with
cause `BindsToRecovery` and no charge against the restart budget
(§7.1). This is the one dependency relationship that recovers by itself.

A `Requires` dependency crashing does not affect a running dependent at
all. The dependent was ordered after it, not coupled to it.

## A dependency that never becomes satisfying

A dependent blocked on a hard dependency waits until its own operation
lifetime expires, and then fails. The timeout is measured from when the
operation was created rather than from when it started running, so a
service queued behind a slow dependency can exhaust its `StartTimeout`
without ever having attempted to start — which is the honest answer, in
that the caller really has been waiting that long.
