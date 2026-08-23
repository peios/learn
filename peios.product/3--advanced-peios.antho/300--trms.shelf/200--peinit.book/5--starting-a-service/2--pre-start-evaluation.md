---
title: Pre-Start Evaluation
description: Evaluating conditions and asserts before anything is forked — the two check mechanisms, and how results are cached.
---

Before anything is forked, peinit evaluates the service's conditions and
asserts (§3.5). The definition comes from the in-memory cache, so this
never touches the registry.

1. Conditions are evaluated. Any failure transitions the service to
   Skipped and abandons the start. Skipped satisfies dependents.
2. If every condition passed and the service has asserts, they are
   evaluated. Any failure transitions the service to Failed with cause
   `AssertionError` and abandons the start.

Only when both pass does the pre-exec sequence continue.

## Where the transition happens

For a fresh start from Inactive, the evaluation gates the transition:
the service becomes Starting only after the checks pass, so a skipped
service goes straight Inactive → Skipped.

For an activation that is already Starting — the start leg of a restart,
for instance — the transition has already happened, and the evaluation
gates further progress instead. A restart whose conditions no longer
hold therefore passes through Starting on its way to Skipped, where a
fresh start would not.

## Two check kinds, two mechanisms

`registry:` checks resolve against the in-memory model. Since a
non-cacheable key is rejected when the definition is read, this
evaluation never needs a live read.

Filesystem checks — `path:`, `file:`, `directory:` — run in a forked
helper. peinit clones it with `CLONE_PIDFD | CLONE_INTO_CGROUP` into the
service's `checks/` sub-cgroup, exactly as it launches anything else.
The helper stats the paths and writes the results to a non-blocking
pipe; peinit watches the pipe and the helper's pidfd through epoll.

`PreStartCheckTimeout` bounds the helper, at 5 seconds by default. On
expiry every check still outstanding is marked **not satisfied** — the
fail-safe direction — and re-evaluated on that basis, so a condition
skips the service and an assert fails it. peinit then kills the helper's
cgroup and unregisters the result descriptor.

A helper that survives the kill, stuck in uninterruptible sleep, has its
cgroup abandoned and recorded exactly as a leaked hook or health cgroup
is (§5.7).

## Caching

The results are computed once, before the service's dependencies are
started, and reused for the rest of that activation. A service that
waits a long time on a dependency starts on the answer that was true
when the wait began.

Filesystem checks are gathered in one helper run, from the conditions.
A service that declares filesystem checks in both `Conditions` and
`Asserts` therefore has results for the conditions' paths and none for
the asserts'; a check with no result counts as not satisfied.
