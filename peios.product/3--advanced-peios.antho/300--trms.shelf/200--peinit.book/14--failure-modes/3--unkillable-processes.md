---
title: Unkillable Processes
description: A process in uninterruptible sleep ignores SIGKILL — what Abandoned means, and the generational escape that lets peinit move on.
---

A process in uninterruptible kernel sleep does not respond to SIGKILL.
Nothing peinit can do will make it exit, and the design consequence is
that peinit stops trying rather than blocking on it.

Detection is uniform: after sending the kill, arm a post-kill deadline
(5 seconds by default) and check whether the cgroup still reports as
populated when it fires.

What follows depends on which cgroup it was:

| Cgroup | Consequence |
|---|---|
| `main/` | The service goes to Abandoned with cause `ProcessUnkillable`. Supervision stops; the cgroup is leaked. |
| `health/` or `hooks/` | The sub-cgroup is orphaned and recorded as a leak. The service carries on normally. |
| `checks/` | The sub-cgroup is dropped with no record. |

The distinction is about what the stuck process is holding. A main
process holds the service's ports, locks and connections, so a service
whose main process cannot be killed cannot be restarted into a working
state. A health check or a hook holds nothing, so a stuck one is a
nuisance rather than a blocker.

## What Abandoned means

peinit has given up. The service is not restarted, does not satisfy
dependents, and every lifecycle command against it is invalid except
`reset` (§10.3).

A `reset` re-checks `main/`. If it has finally emptied — the I/O that
was hung completed, or the device came back — peinit cleans up the whole
tree and the service returns to Inactive. If it is still populated, the
service returns to Inactive anyway, the cgroup stays leaked, and both the
acknowledgement and the console carry a warning saying so.

## The generational escape

A leaked cgroup cannot be removed, so the next start would collide with
it. Recording a leak increments the service's cgroup generation, and the
next start builds a fresh tree at `.gen<N>` (§5.1). Old trees persist
until reboot.

That is what lets a service recover from a leak at all: peinit cannot
clean up the old tree, so it stops trying to and uses a new one.

## What it actually means

Every path here has the same underlying cause. Something below the
service — a hung mount, a failing controller, a device that stopped
answering — is not responding to the kernel, and no amount of restarting
the service will change that. The leak record exists to say so, because
the alternative is a service that mysteriously will not restart.
