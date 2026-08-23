---
title: Triggers
description: What makes a service start by itself — the trigger kinds, how arity is enforced, and how the set is extended.
---

A trigger says when a service starts by itself. Triggers are independent
of service type: a Simple service can have a timer, and a Oneshot can
start at boot.

`Triggers` is a multi_string, each entry either `type` or
`type:argument`.

| Trigger | Form | Meaning |
|---|---|---|
| Boot | `boot` | Start during the Phase 2 boot sequence. |
| Deferred boot | `boot:settled` | Start once the boot set has settled, or the deadline expires. §2.5 |
| Timer | `timer:<schedule>` | Start on a schedule. §9.1 |

A service with no triggers is demand-only: it starts only when something
asks for it, whether an administrator, a dependency, or an `OnFailure`
handler.

Multiple triggers of the same type are allowed. A service with
`["timer:*-*-* 02:00:00", "timer:*-*-* 14:00:00"]` runs at 2am and 2pm,
and each trigger is independent — its own timerfd, its own next-firing
computation, its own history.

## Arity is enforced

`boot` takes no argument. `boot:<something>` accepts only the
sub-triggers in the table above, and any other value is malformed rather
than an unknown trigger type to be ignored. `timer` with no schedule is
malformed, as is `timer:` with an empty one.

That strictness is the point. Unknown *values* on a service key are
ignored for forward compatibility, and if unknown trigger types were
ignored too, `boot:setled` would be silently accepted and the service
would simply never start. Instead it fails to decode, loudly.

## Disabled

`Disabled=1` suppresses automatic activation and nothing else. No
trigger fires: not `boot`, not `boot:settled`, not a timer, and not any
trigger type added later. A disabled service's timers are neither armed
nor serviced.

The definition is still loaded into the in-memory model, and an explicit
start still works. To stop a service being started at all, deny
`SERVICE_START` in its `ServiceSecurity` descriptor — that is an access
control question, not a trigger question, and answering it with the
`Disabled` flag would mean a flag that anyone who can write the key can
clear.

Enabling and disabling are registry writes performed by administrative
tools, not peinit commands. peinit picks the change up through a
registry change notification, or on the next reload-config.

## Extensibility

The `type:argument` shape is designed to grow. Path, device and event
triggers slot into the same array with no schema change, because a
trigger is a string in a list rather than a field of its own.
