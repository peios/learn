---
title: Readiness Levels
description: How a service waits for a condition inside another service — Requires = ["netd:routed"] — and why a level is exact, per-publisher and never stale.
---

> [!WARNING]
> **Incomplete in this version.** Publishing works and the syntax is
> accepted, but the start gate does **not** yet hold: a service whose
> required level never arrives starts anyway. Do not rely on
> `Requires = ["<service>:<level>"]` to keep a service back. See
> [what is not finished](#what-is-not-finished).

`network-online.target` on systemd is famously meaningless, because
"online" has no single definition. A service needing a default route and
a service needing only a loopback address want different things, and one
target cannot mean both.

peinit does not have an online target. A service says what it is waiting
for, in the publisher's own vocabulary:

```
Requires = ["netd:routed"]
Wants    = ["timed:synchronised"]
```

`netd:routed` waits for netd to be active **and** to have published the
level `routed`. `netd` on its own is unchanged — the ordinary "that
service must be active" dependency.

## The syntax

`<service>:<level>`, split on the first colon. It rides on the existing
`Requires`, `Wants` and `BindsTo` fields rather than a field of its own,
because a level dependency *is* a service dependency with a stricter
predicate: `netd:routed` subsumes `netd`. Each relationship keeps exactly
the semantics [it already has](~peios/advanced-peios/peinit/dependencies/relationships), applied to
the stricter test.

It cannot collide with a service name. A service name may contain only
letters, digits, `.`, `_` and `-`, so a colon never appears in one, and
no existing definition can accidentally become a level dependency.

A trailing colon — `"netd:"` — reads as a plain dependency on `netd`. It
is a typo, and treating it as a request for the empty level would produce
a condition nothing could ever satisfy.

## How a level gets there

The service publishes it on the notification channel it already has, as
`LEVEL=` beside `READY=1` and `STATUS=`:

```
LEVEL=routed
```

An empty value retracts it. peinit records the level against the sending
service, and holds any dependent whose declaration does not match.

There is no subscription. peinit does not connect to netd's socket or
timed's, does not need to find them before they exist, and carries no
knowledge of their wire formats — which matters, because PID 1 is the one
process on the machine that cannot afford to fail to start.

## Levels are exact, not ordered

`Requires = ["netd:addressed"]` is **not** satisfied by `netd:routed`.

peinit has no ordering over another daemon's vocabulary and does not
invent one. netd knows that `routed` implies `addressed`; peinit does
not, and a central table of which levels imply which would recreate
exactly the coupling that naming levels after their publisher avoids.

A service that genuinely wants "addressed or better" should depend on the
level it actually needs. If a publisher's levels are ordered in a way
dependents keep needing to express, that is a sign the publisher should
name the useful condition directly.

## A level is never stale

peinit clears a service's level whenever that service leaves a state that
satisfies dependents. A level is a claim about a process that is
currently making it, and one that outlived its process would hold a
dependent open on a promise nobody was keeping — the exact failure the
mechanism exists to prevent.

Because peinit is the process that notices a service exiting, this needs
no timeout and no liveness check.

## What is not finished

The gate does not hold yet, and a service declaring a level it will never
get starts regardless.

The reason is structural rather than a missing check. peinit's start plan
has three answers about a dependency — *satisfied* (proceed), *startable*
(start it, then proceed), *missing* (block) — and an unmet level is none
of them. It is a condition that may arrive later, on a service that is
already running and that starting again would not help. The ordinary
`Requires` wait works because peinit starts the target and waits for it to
reach Active; a level has no equivalent event in the plan, so the
dependent has to be re-checked at dispatch rather than decided at plan
time.

Until that lands, treat a level as documentation of intent.

## What happens on a drop

Nothing, in this version. If a level falls away after a dependent has
already started, the dependent keeps running and is not told.

That is a deliberate limit, not an oversight. The notification channel is
one-way by specification (PSPU §4.16), so peinit has no way to tell a
running service anything. A service that needs to react to a level
changing while it runs should subscribe to the publisher directly — which
is what resolvd does with netd today, and what any consumer that cares
that much will want anyway, since it will need the detail rather than
just the fact.

peinit's contribution is the start gate: the moment when the service does
not exist yet and so cannot subscribe to anything at all.

## Published levels

| Publisher | Levels |
|---|---|
| [netd](~peios/networking/overview) | `link` → `addressed` → `routed` |
| [timed](~peios/time/overview) | `unsynchronised`, `settling`, `synchronised`, `spike` |

Any service may publish a level; nothing about the mechanism is specific
to these two. The vocabulary is the publisher's own, and needs no
registration.
