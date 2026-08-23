---
title: Leaked Sub-Cgroups
description: A D-state process does not die when SIGKILLed — what happens to its cgroup, and how the leak becomes visible.
---

A process in uninterruptible kernel sleep — D-state, typically a hung
NFS mount or a failing disk controller — does not die when it is
SIGKILLed. Its cgroup cannot be removed while it is there.

peinit detects this through `cgroup.events`: after sending the kill it
arms a post-kill deadline, 5 seconds by default, and checks whether
`populated` is still 1 when the deadline fires.

## What happens depends on which cgroup it is

For the **main process**, a survivor is fatal to supervision: the
service transitions to Abandoned with cause `ProcessUnkillable` and
peinit stops supervising it (§6.1).

For a **health check or a hook**, it is not. Those are diagnostic and
setup processes; they hold no service resources — no ports, no file
locks, no database connections — so a stuck one does not make the
service unmanageable. peinit orphans the sub-cgroup instead:

1. Marks it leaked, recording the path, the kind and the time.
2. Increments the service's cgroup generation, so the next start builds
   a fresh tree (§5.1).
3. Carries on supervising the service normally.

A leaked **pre-start check helper** is dropped without a record.

The leaked cgroup stays in the hierarchy until the next reboot.

## Visibility

Leaks are not silent, but they are pull rather than push: peinit tracks
them per service and exposes them, rather than emitting a log line or an
event when one is recorded.

- A **status query** includes a `warnings` array, one entry per leak,
  each an object with the sub-cgroup path, its kind, and the time of
  detection:

  ```json
  {"path": "/sys/fs/cgroup/peinit/jellyfin/health", "type": "health", "detected_at": "2026-06-01T12:34:56.123456789Z"}
  ```

  The `type` is `health` for a leaked `health/` sub-cgroup, `hooks` for
  a leaked `hooks/` one, and `service_tree` for a leaked service root —
  the last being the most serious, since it means the whole tree
  including `main/` could not be reclaimed.

- A **start command** on a service with leaks returns a warning in its
  acknowledgement, saying the service has leaked sub-cgroups from a
  previous generation and that this indicates an I/O problem needing
  investigation.

Either way, what the leak means is the same: something underneath the
service is not responding to the kernel, and no amount of restarting the
service will fix it.
