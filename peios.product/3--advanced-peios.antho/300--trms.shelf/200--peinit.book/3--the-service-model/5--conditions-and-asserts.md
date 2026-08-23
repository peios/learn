---
title: Conditions and Asserts
description: Two start-time checks in the same form over the same four check types, differing only in what a failure means.
---

Both are start-time checks in the same `type:argument` form, over the
same four check types. What differs is the consequence of a failure.

| Check | Form | Passes when |
|---|---|---|
| path | `path:<path>` | The path exists, of any type. |
| file | `file:<path>` | A regular file exists there. |
| directory | `directory:<path>` | A directory exists there. |
| registry | `registry:<key>` | The registry key exists. |

**Conditions** describe when a service *applies*. A failed condition
skips the service: it transitions to Skipped, which satisfies its
dependents, because a service that does not apply has succeeded by not
needing to run.

**Asserts** describe what a service *needs*. A failed assert fails the
service, with cause `AssertionError` — the service was expected to run
and a precondition it depends on is missing.

All entries of a kind are AND'd. Conditions are evaluated first; asserts
only if every condition passed. Both are evaluated before dependency
resolution and before any pre-exec hook, and an entry with an empty
argument or an unrecognised type is a decode error.

## Evaluation without blocking

peinit is single-threaded PID 1 and its event loop cannot block while a
check runs. Two constraints follow, and they are why the check types
behave differently from one another.

### Registry checks are cache-only

A `registry:` check is evaluated against the in-memory model, never by a
live registry read. It can therefore only name a key peinit already
caches — under `Machine\System\Services\` or `Machine\System\Init\`.
Naming any other key is a decode error, caught at load rather than at
start.

Within that, resolution is narrower than the load-time check suggests.
A `registry:Machine\System\Services\<name>` check is true when that
service exists in the model, which makes it a subkey-existence test
rather than a general key-existence test.

### Filesystem checks run in a helper

`stat()` can block uninterruptibly on hung I/O — a dead NFS mount, a
failing disk controller — so peinit does not call it from the event
loop. It forks a short-lived helper into a dedicated `checks/` cgroup
under the service's tree, using the same `clone3` path as any other
child. The helper stats the paths and reports over a non-blocking pipe;
peinit waits on the pipe and the helper's pidfd through epoll, and never
blocks.

`PreStartCheckTimeout`, default 5 seconds, bounds the helper. A check
that does not report in time is treated as **not satisfied** — the
fail-safe direction, so a condition skips the service and an assert
fails it. peinit then SIGKILLs the helper's cgroup and unregisters the
result descriptor, and the event loop is never held up by a hung check.

## When results are computed

Checks are evaluated once, before the service's dependencies start, and
the result is cached for the rest of that activation. A service that
waits a long time for a dependency starts on the answer that was true
when the wait began, not on a fresh one.
