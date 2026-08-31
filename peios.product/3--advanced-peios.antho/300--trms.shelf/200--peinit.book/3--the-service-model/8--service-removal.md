---
title: Service Removal
description: What happens when a definition disappears from the registry, depending on whether the service is running.
---

When a definition disappears from `Machine\System\Services\`, peinit
learns of it through the ordinary change-notification path. What happens
next depends on whether anything is running.

## Not running

An entry in Inactive, Failed, Completed, Skipped, Abandoned or **Backoff**
is discarded immediately. There is no process to consider.

Backoff belongs in this list rather than the next one, which is not
obvious: a service between restart attempts looks like it has something
pending. It does not. It has no process, and once the definition is gone
there is nothing left to restart it from, so there is neither an instance
to supervise nor a restart to wait for.

## Running

An entry in Active, Starting, Reloading or Stopping is **not**
killed. The running process is a job, and a job's lifecycle is
independent of the definition that produced it — removing a definition
stops future management, it does not terminate work in progress.

peinit marks the entry **definition-removed** and keeps the cached
definition, solely to go on supervising the instance it already has.
When that instance exits it is not restarted — `RestartPolicy` is moot,
because there is nothing left to restart from — and peinit then discards
the entry.

While an entry is definition-removed:

- it keeps satisfying its dependents for as long as the instance is
  alive, because it is still running;
- `stop` is accepted, so an administrator can drain it cleanly, using
  the cached `StopTimeout`;
- `start`, `restart` and `reload` are rejected with `UNKNOWN_SERVICE` —
  there is no definition to work from;
- `status` reports the current runtime state with `definition_removed`
  set, so the draining instance is visible rather than silent.

`definition-removed` is a flag on the existing runtime state, not a
state of its own. The state machine (§6.1) and the command × state
matrix (§10.3) are unchanged by it.

Once the instance exits or is stopped, the entry — including anything in
its fd store (§10.6) — is discarded. A crash counts: the exit is routed
to Failed rather than into a restart, because there is no policy left to
apply. The fd store goes with it, which a crash would otherwise preserve
for the restart that is not going to happen. A dependent that `Requires` the
removed service keeps being satisfied while the instance runs; after the
entry is discarded, the dependent's next start sees an unresolved
dependency and takes the ordinary validation path.
