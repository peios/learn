---
title: The Cgroup Tree
description: peinit uses cgroups v2 for exactly two things — knowing which processes belong to a service, and killing them all at once.
---

peinit uses cgroups v2 for exactly two things: knowing which processes
belong to a service, and killing all of them at once. It does no
resource accounting and sets no limits.

Every service gets a tree:

```
/sys/fs/cgroup/peinit/<cgroup-id>/          service root
/sys/fs/cgroup/peinit/<cgroup-id>/main/     the main process
/sys/fs/cgroup/peinit/<cgroup-id>/hooks/    hooks and reload commands
/sys/fs/cgroup/peinit/<cgroup-id>/health/   health check invocations
/sys/fs/cgroup/peinit/<cgroup-id>/checks/   pre-start filesystem check helpers
```

The sub-cgroups satisfy cgroups v2's "no internal processes" rule, which
applies whenever controllers are enabled, and give hooks and probes
containment of their own so that killing one does not touch the service.

They are not all created at once. The root and `hooks/` are created when
the first thing needs them — the first pre-exec hook, if there is one —
and `main/` and `health/` when the main process launches.

## The cgroup id

`<cgroup-id>` is the service name with every byte outside
`[A-Za-z0-9._-]` percent-encoded as `%` plus two uppercase hex digits.
Service names are already restricted to that set (§3.1), so in practice
the id equals the name.

The encoding is a defensive guarantee that distinct names always map to
distinct, cgroup-safe ids. `%` is not itself in the safe set, so it
escapes to `%25` and the encoding is prefix-free. That is what makes it
injective, unlike a plain substitution of `/` for `-`, under which `a/b`
and `a-b` would collide.

The id is internal. The name a user sees is unchanged.

## Generations

A cgroup whose processes survived SIGKILL cannot be removed — `rmdir` on
it fails with `EBUSY`. When peinit detects that a service's tree still
has live processes after the post-kill deadline, it records the leak and
increments the service's cgroup generation. The next start uses a fresh tree:

```
/sys/fs/cgroup/peinit/<cgroup-id>.gen<N>/
```

Old leaked trees persist until the next reboot.

The generation counter advances once per recorded leak rather than once
per restart, and leaks are deduplicated by path and kind. A single
failed start can record two — one for `hooks/` and one for the service
tree — so the number can advance by more than one at a time.

Because `.` is a legal character in a service name and the generational
suffix uses one, the tree *path* is not injective the way the id is: a
service literally named `app.gen1` and generation 1 of a service named
`app` resolve to the same directory.
