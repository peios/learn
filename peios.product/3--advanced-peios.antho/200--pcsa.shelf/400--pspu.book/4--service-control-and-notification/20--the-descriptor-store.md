---
title: The Descriptor Store
description: Handing file descriptors to the manager and getting them back after an unchosen restart — storing, removing, returning, and when the store is emptied.
---

A service may hand file descriptors to the manager and get them back
after a restart it did not choose. This is what lets a stateful daemon —
one holding a listening socket, say — restart without dropping what it
already had.

The manager MUST support a per-service maximum, which MAY be zero. Zero
disables the store for that service, and a service MUST NOT assume a
store exists.

## Storing

On an authenticated datagram carrying `FDSTORE=1` with descriptors
attached, the manager MUST:

1. If the store is disabled for this service, **close** the descriptors
   and record the rejection.
2. If the store already holds its maximum, **close** the descriptors and
   record the rejection. It MUST NOT evict an existing entry — a full
   store is full, and silently discarding something the service is
   relying on to survive a restart would be worse than refusing the new
   one.
3. Store them under the value of `FDNAME` if present and non-empty, and
   under the name `stored` otherwise.
4. Note `FDPOLL=0` if present.

A datagram MAY carry several descriptors. Each becomes its own entry
under the one name, and each is independently subject to the maximum —
so a datagram carrying more than will fit has some stored and the rest
closed.

Several entries MAY share a name.

`FDPOLL=0` asks the manager not to monitor the descriptors for error
conditions. A manager MAY monitor stored descriptors and remove ones
that have become invalid; a manager that does not MUST still accept the
field.

## Removing

`FDSTOREREMOVE=1` with `FDNAME` MUST remove every entry of that name and
close its descriptors. A name matching nothing is a no-op and MUST NOT
be an error.

`FDSTOREREMOVE=1` **without** `FDNAME` MUST be treated as a malformed
line, rejecting the whole datagram (§4.17). A remove with no name has no
defined meaning, and the alternative readings — remove everything,
remove the default name, do nothing — are far enough apart that guessing
between them silently is worse than refusing.

## Returning them

When the service starts again, the manager MUST pass the stored
descriptors to the new process:

1. Placed consecutively, starting at descriptor **3**, with close-on-exec
   cleared.
2. `LISTEN_FDS` set to the number of descriptors passed.
3. `LISTEN_FDNAMES` set to the names, **colon-separated**, in the same
   order as the descriptor numbers.
4. `LISTEN_PID` set to the new process's own PID.
5. The store cleared.

`LISTEN_PID` is what lets a service verify that the variables are
addressed to it rather than inherited from an ancestor. A conforming
client checks it against its own PID before trusting `LISTEN_FDS`, and
treats a mismatch as meaning no descriptors were passed — so a manager
that omits it hands descriptors to a service that will not take them.

All four variables MUST be absent when no descriptors are passed, and
the manager MUST NOT allow any of them to be set by a configurable
environment layer. A `LISTEN_FDS` reaching a service that was passed
nothing points its descriptor-adopting code at whatever happens to be at
descriptor 3.

Descriptors are returned to the service's main process only. A hook or a
probe MUST NOT receive them.

The store MUST be cleared once the descriptors have been passed. The
manager MUST NOT clear it when a start attempt fails before that point —
the descriptors are still the service's, and the next attempt should get
them.

## When the store is emptied

The manager MUST clear the store, closing its descriptors, when:

- the service is stopped deliberately — by a client, or as part of a
  system shutdown; or
- the service's definition is withdrawn and its entry is finally
  discarded.

The manager MUST NOT clear it on a restart the service did not ask for —
a crash, or a restart policy acting on one. That case is the entire
purpose of the mechanism: the descriptors survive exactly the restart
the service could not prepare for.

> [!NOTE]
> `LISTEN_FDS`, `LISTEN_FDNAMES` and `LISTEN_PID` are the convention
> established by systemd's `sd_listen_fds`, and are specified here in
> the same form deliberately. Software already written to adopt
> descriptors that way works against a Peios service manager without
> modification.
