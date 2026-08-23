---
title: Command Outcomes by State
description: The defined answer for every command sent to a service in an unexpected state — the manager never silently does nothing.
---

A command sent to a service in an unexpected state MUST receive a
defined answer. The manager MUST NOT silently do nothing.

| | inactive | starting | active | reloading | stopping | completed | backoff | failed | abandoned | skipped |
|---|---|---|---|---|---|---|---|---|---|---|
| `start` | act | merge | already | already | queue | act | defer | act | invalid | act |
| `stop` | noop | cancel + act | act | act | merge | clear | cancel | noop | invalid | noop |
| `restart` | act | queue | act | act | queue | act | act | act | invalid | act |
| `reload` | invalid | invalid | act | merge | invalid | invalid | invalid | invalid | invalid | invalid |
| `reset` | noop | invalid | invalid | invalid | invalid | invalid | invalid | clear | clear | clear |
| `status` | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok |

## The outcomes

**act** — create an operation and execute it. The manager returns the
acknowledgement shape.

**merge** — an operation of this type is in flight. The command merges
into it (§4.11) and the caller receives that operation's identifier.

**queue** — the operation is created and left pending; it executes once
the operation ahead of it completes. The caller receives the new
operation's identifier.

**defer** — an automatic restart is already pending for this service.
The manager MUST create a pending start operation, or merge into a
deferred one that already exists, and MUST NOT execute it until the
existing delay has elapsed. A `start` MUST NOT shorten a pending
restart's delay.

**already** — the service is in the state the command would take it to
and no operation of this type is in flight. The manager MUST return the
**status** shape, not an error and not an acknowledgement.

**noop** — the command has no effect. The manager MUST return the status
shape.

**clear** — the service returns to inactive. This is a synchronous
outcome; the manager returns an acknowledgement.

**cancel** — abort or cancel the operation in flight, then proceed.

**invalid** — the command is not valid for this state. The manager MUST
answer `INVALID_STATE`.

**ok** — `status` is answered from any state.

## The `backoff` column

A service in `backoff` is down with an automatic restart pending, and
the four lifecycle commands mean different things there:

- `start` defers, as above, and honours the remaining delay.
- `stop` cancels both the pending restart and any deferred start, and
  the service becomes inactive.
- `restart` cancels the automatic restart and performs a
  caller-initiated one.
- `reload` and `reset` are invalid: there is no process to reload and no
  terminal state to clear.

## The `abandoned` column

Every lifecycle command except `reset` is invalid on an abandoned
service. `reset` clears it. Nothing else is meaningful while processes
the manager could not terminate are still present.

## A service being withdrawn

A manager MAY keep supervising a service whose definition has been
removed while an instance of it is still running. In that condition the
manager MUST answer `start`, `restart` and `reload` with
`UNKNOWN_SERVICE`, MUST accept `stop`, and MUST report the condition in
the status shape (§4.14). This holds whatever the service's state.
