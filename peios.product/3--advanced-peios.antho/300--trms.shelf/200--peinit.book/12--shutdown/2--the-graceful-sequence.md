---
title: The Graceful Sequence
description: The ordered steps of a graceful shutdown, from entering the shutdown state to the final power action.
---

## Step 1: Enter the shutdown state

peinit sets an internal flag. While it is set, no new service starts,
and control commands other than `status`, `list` and `operation-status`
are rejected as invalid for the current state.

Every live submitted job (§8.5) is stopped at this point too: SIGTERM
to each — unless it has already sent `STOPPING=1` — with cause
`shutdown`, its own `stop_timeout` to the kill, and no ordering between
jobs or against the service waves, because a job has no dependencies
to order by. A job still queued for launch is cancelled with the same
cause. `submit` is refused for the rest of the shutdown; `status`,
`wait`, `stop` and `signal` keep answering, as do the control socket's
`job-status`, `job-list` and `job-stop`.

Timer triggers are not disarmed. A calendar timer that fires during the
shutdown window is still classified and acted on: for a service in
Inactive, Completed or Failed — precisely the states step 3 classifies
as not participating — that means creating a start operation and
starting the service. The shutdown plan was fixed when the shutdown
began, so a service started this way is in no wave, is not waited for,
and is not reached by the global-timeout sweep.

## Step 2: Suspend Critical failure semantics

A Critical service failing during shutdown is recorded but does not
trigger a reboot. The system is already going down, and rebooting from
here would loop.

## Step 3: Classify

Completed services — Oneshots with `RemainAfterExit` — have no process
and are transitioned to Inactive, releasing the dependency
relationships they were holding so their dependents can be stopped
cleanly.

The rest are classified for stop eligibility:

- **Active and Reloading** are graceful-stop eligible and enter the
  waves.
- **Stopping** services are already on a stop path. They join the waves
  for ordering and timeout purposes, but do **not** receive another
  SIGTERM.
- **Starting** services are not eligible. peinit cancels the startup,
  SIGKILLs the service cgroup if one exists, and transitions them to
  Failed with cause `ShutdownWave` while post-kill verification is
  pending. A cgroup still populated after the post-kill timeout takes
  the service to Abandoned with cause `ProcessUnkillable` and the cgroup
  is leaked. A Starting service whose job never forked skips the check
  and goes straight to Failed.
- **Inactive, Failed, Skipped, Backoff and Abandoned** do not
  participate. Abandoned cgroups stay leaked and shutdown continues.

## Step 4: Stop in reverse dependency order

peinit builds the reverse dependency graph over hard dependencies and
stops in waves:

1. Each eligible service receives SIGTERM. Already-stopping ones do not.
2. Each has `StopTimeout` to exit.
3. On expiry, SIGKILL to the service's entire cgroup.
4. No service is stopped until everything depending on it has stopped.

A service that sent `STOPPING=1` does not receive a SIGTERM at all: it
has already said it is shutting down, and peinit goes straight to the
stop deadline.

### Timing an already-stopping service

peinit does not reset an already-Stopping service's clock, either when
shutdown begins or when its wave becomes eligible. It uses the timing
evidence retained from the stop path that put the service in Stopping:

- If a Stop operation, or a Restart executing its stop leg, is in
  flight, that operation's retained timing governs.
- Otherwise peinit uses service-level evidence, which carries the cause
  that initiated the transition — `ExplicitStop`, `ShutdownWave`,
  `ConflictEviction` or `BindsToPropagation`.

peinit requires the evidence to be present, to belong to a service
actually in Stopping, to carry a cause matching the service's current
cause, to name one of those four causes, and not to describe a deadline
earlier than its own start. Evidence that is missing, stale or
ambiguous **fails closed** rather than being guessed at — and it fails
the whole shutdown, not just that participant, so a shutdown command
with one such service is refused, and one discovered on a later wave
ends the runtime loop.

An operation whose lifetime expires while it is still Pending — a
later-wave stop waiting for its dependencies — fails that operation and
its waiters. It does **not** authorise signalling the service before its
wave is eligible. Shutdown owns the signalling; the operation object is
an observation of it.

## Step 5: Global timeout

| Key | Default | Meaning |
|---|---|---|
| `Machine\System\Boot\ShutdownTimeout` | 90 | Seconds for the whole sequence. |
| `Machine\System\Boot\PostKillTimeout` | 5 | Seconds for a cgroup to drain after SIGKILL. |

On expiry, every remaining participant's cgroup is killed, anything that
does not drain within the post-kill timeout is marked Abandoned with its
cgroup leaked, and shutdown continues regardless. Live submitted jobs
are killed in the same sweep, whatever phase their stop had reached,
and abandoned on the same terms.

The sequence does not move to step 6 while a submitted job is live. A
job's reap advances shutdown progress exactly as a service's does, so a
session that exits promptly on SIGTERM costs the shutdown nothing, and
one that does not costs it `stop_timeout` and the post-kill grace.

## Step 6: Save the random seed

After every service has stopped and before any unmount, peinit writes a
fresh seed to `/var/state/peinit/random-seed` for the next boot: 512
bytes from the kernel CSPRNG on this machine, never copied from an
image, protected so that only SYSTEM-equivalent authority can read or
replace it.

The write is crash-conscious: a temporary file on the same filesystem,
written, flushed, atomically renamed over the old seed, and the
containing directory flushed. A failure is recorded and shutdown
continues.

The forced and Critical-reboot paths skip it, along with the unmount
step, and go directly to sync and the final action.

## Step 7: Unmount

1. Snapshot the mount table first, from `/proc/self/mountinfo`.
2. Attempt to unmount every remaining non-root mount in the namespace —
   not only what peinit mounted, so the Phase 1 set is covered by
   construction.
3. Process in descending path depth, so children go before parents.
4. A mount point already gone is a successful no-op.
5. On failure, attempt a read-only remount. If that fails too, record it
   and continue.
6. The root is never unmounted, but is remounted read-only at the end. A
   failure there is recorded and does not stop step 8.

## Step 8: Sync and the final action

This step is irreversible. Cleanup failures retained from steps 6 and 7
affect diagnostics only and never block it.

1. `sync()`. Called on all three paths — graceful, forced and
   Critical reboot.
2. `reboot(2)` with `RB_POWER_OFF`, `RB_AUTOBOOT` or `RB_HALT_SYSTEM`.
3. If `reboot(2)` returns, the final action failed. peinit enters a
   minimal failed-shutdown state, keeps PID 1 alive, records the
   failure, and retries the same action no more than once a second. It
   does not restart services and does not enter recovery mode —
   finalisation has begun and there is nothing to go back to.

## Shutdown during boot

A shutdown requested while Phase 2 is still running takes effect
immediately, through the same classification: Starting services are
SIGKILLed, services that reached Active are stopped gracefully, and the
boot is abandoned.
