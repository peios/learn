---
title: The Command × State Matrix
description: The defined answer for every command sent to a service in an unexpected state, including backoff, abandoned and definition-removed services.
---

A command sent to a service in an unexpected state gets an answer, not a
silent no-op. What the answer is depends on the pair.

| | Inactive | Starting | Active | Reloading | Stopping | Completed | Backoff | Failed | Abandoned | Skipped |
|---|---|---|---|---|---|---|---|---|---|---|
| start | Start | MERGE | ALREADY | ALREADY | QUEUE | Start | DEFER | Start | ERROR | Start |
| stop | NOOP | Cancel+Stop | Stop | Stop | MERGE | Clear | Cancel | NOOP | ERROR | NOOP |
| restart | Start | QUEUE | Restart | Restart | QUEUE | Start | Restart | Start | ERROR | Start |
| reload | ERROR | ERROR | Reload | MERGE | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR |
| reset | NOOP | ERROR | ERROR | ERROR | ERROR | ERROR | ERROR | Clear | Clear | Clear |
| status | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |

**ALREADY** — the service is already where the command would take it and
no operation of that type is in flight. peinit returns the current
status rather than an error.

**MERGE** — an operation of that type is already running. The command
merges into it; the caller receives that operation's identifier and, if
waiting, blocks on its outcome.

**DEFER** — create a Pending start operation but do not execute it until
the existing backoff deadline expires. A deferred start already present
is merged into.

**QUEUE** — the operation is queued Pending and executes after the
current one completes.

**NOOP** — the command has no effect. peinit returns the status.

**ERROR** — the command is invalid for the state.

**Clear** — reset to Inactive.

**Cancel** — abort the current operation, then proceed.

## The Backoff column

Backoff is the interesting one, because the service is down with an
automatic restart already pending.

- `start` creates or merges into a **deferred** start operation and
  honours the remaining delay. It does not short-circuit the backoff.
  If the automatic restart later becomes due, it merges into the
  administrator's operation, so the identifier the caller holds is the
  one that executes.
- `stop` cancels both the pending restart and any deferred start, and
  the service goes Inactive. A subsequent automatic restart is refused,
  because the service is no longer in Backoff.
- `restart` cancels the automatic restart and queues an
  administrator-initiated one.
- `reload` and `reset` are invalid: there is no process to reload, and
  no terminal state to clear.

## The Skipped column

`start` and `restart` clear Skipped before they run. A Skipped service
is not in a state a start can proceed from — the state machine permits
`Skipped -> Inactive` and nothing else — so the activation performs that
transition first, then re-evaluates the conditions from scratch. Both
outcomes are possible: the precondition that was missing at boot may now
hold, in which case the service starts; or it may still not, in which
case the service is skipped again, for whatever reason applies now.

The clear is reported like any other transition, so a console watching
the service sees it leave Skipped rather than appearing to jump.

`reset` also clears Skipped, and differs only in stopping there.

## The Abandoned column

Every lifecycle command is invalid on an Abandoned service except
`reset`, which clears it (§6.2). Nothing else is meaningful while
processes that ignored SIGKILL are still in the cgroup.

## Definition-removed services

Independently of state, a service whose definition has been removed
(§3.8) rejects `start`, `restart` and `reload` with `UNKNOWN_SERVICE`,
accepts `stop`, and reports its state on `status`.
