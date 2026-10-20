---
title: The Channel
description: Attaching to /dev/pkm_registry — the privileges the open handler demands, registration, source slots, resuming a Down slot, and the optional lifetime extension.
---

## The device

A source attaches by opening the character device `/dev/pkm_registry`.

The `open()` handler evaluates the calling thread's effective token.
The caller MUST hold `SeTcbPrivilege` and it MUST be **enabled**, not
merely present; `open()` fails `EPERM` otherwise. An unprivileged
process cannot obtain a descriptor to the device at all.

One open descriptor corresponds to one source connection.

## Registration

Before entering the request loop a source MUST register its hives, by
issuing the `REG_SRC_REGISTER` ioctl on the device fd. The argument is
a `reg_src_register_args`:

| Field | Type | Description |
|---|---|---|
| `hive_count` | `u32` | Number of hive entries. MUST be non-zero. |
| `_pad` | `u32` | Reserved. MUST be zero. |
| `max_sequence` | `u64` | The highest sequence number persisted anywhere in this source's storage. A single value for the whole source, not per hive. |
| `hives_ptr` | `u64` | Userspace address of an array of `hive_count` `reg_src_hive_entry` structures. |

Each `reg_src_hive_entry`:

| Field | Type | Description |
|---|---|---|
| `name_len` | `u32` | Length of the hive name in UTF-8 bytes. |
| `_pad0` | `u32` | Reserved. MUST be zero. |
| `name_ptr` | `u64` | Userspace address of the hive name. Not null-terminated. |
| `root_guid` | `u8[16]` | The GUID of this hive's root key. MUST NOT be all-zero. |
| `flags` | `u32` | `RSI_HIVE_PRIVATE` (`0x01`). All other bits reserved and MUST be zero. |
| `_pad1` | `u32` | Reserved. MUST be zero. |
| `scope_guid` | `u8[16]` | The private scope identifier. MUST be all-zero unless `RSI_HIVE_PRIVATE` is set. |

Each hive carries its own name pointer; there is no separate array of
names.

The kernel validates, and registration fails if any of the following
does not hold:

- every hive name is valid — UTF-8, no null byte, no separator,
  non-empty, within the configured component length;
- no hive name is `CurrentUser` in any casing, which is reserved;
- the route identity of each hive — its case-folded name paired with
  its scope — does not collide with one held by an Active source
  (`EEXIST`);
- no root GUID is all-zero, and the root GUIDs within this request are
  distinct from each other;
- a hive without `RSI_HIVE_PRIVATE` carries an all-zero `scope_guid`;
- `hive_count` is within `MaxHivesPerSource` and the registered source
  count is within `MaxRegisteredSources` (`ENOSPC`);
- `max_sequence` is not `U64_MAX`, since the kernel MUST be able to
  allocate above it (`EOVERFLOW`).

`max_sequence` initializes the kernel's global sequence counter to at
least one above it, so that new writes always outrank anything already
persisted. A source MUST report it accurately; under-reporting it
allows a new write to collide with a stored entry.

## Source slots

A successful registration creates a **source slot**, the kernel object
owning one connection and its hive set. A slot is Active or Down.

Each registered hive has a stable identity: its case-folded name, its
visibility, its scope GUID if private, and its root GUID.

A source crash or an fd close marks the slot Down. It does **not**
unregister the source or retire any hive identity. Down slots keep
their identities reserved, and collision checks include them. There is
no implicit retirement.

While a slot is Down its hives are unavailable; operations needing a
round trip fail, key descriptors held by processes remain valid, and
watches remain armed.

## Resuming a Down slot

A new process MAY take over a Down slot. It MUST hold `SeTcbPrivilege`
and it MUST register **exactly the same hive set**: the same number of
hives, and for each of them the same case-folded name, the same
visibility, the same scope GUID and the same root GUID.

Partial resume is rejected. In particular:

- A request whose only mismatch is a different root GUID for an
  otherwise-matching hive fails `ESTALE`.
- Other partial or malformed resume attempts fail `EINVAL`.
- A collision with an **Active** slot fails `EEXIST`, and takes
  precedence over `ESTALE` when both would apply.

A source MUST NOT expect to add hives by resuming a Down slot with a
larger set; that is a partial-resume failure. New hives require a new
slot.

The kernel authenticates a replacement by `SeTcbPrivilege`, not by
process identity. Process identity cannot survive a crash and restart,
so nothing records or compares it.

On a successful resume the slot becomes Active and the kernel replays
any pending layer deletions before resuming normal traffic.

## Before serving anything

A source MUST purge orphaned key records before completing
registration. An orphaned record is a key with no path entry in any
layer, left behind by a key that was unlinked but not dropped before
the previous shutdown.

If that cleanup cannot be completed, the source MUST fail registration
rather than become Active with known orphans. The kernel does not
verify this and cannot: it has no independent view of the source's
storage.

On first boot against an empty store, a source MUST create a root key
record for each hive it backs, generating a GUID for each and giving it
an appropriate default Security Descriptor, and MUST persist them. The
root GUIDs it then reports in registration are those. Subsequent
startups reuse the persisted ones.

## The lifetime extension

A source MAY negotiate the lifetime extension. It tells the source how
long each request and transaction may live, and gives it a lease that
proves a transaction still has a live kernel-side owner. The RSI request
and response frames are unchanged by it. A source that does not
negotiate it gets the protocol described in the rest of this book.

All three ioctls are issued on the device fd. Every timestamp is an
absolute `CLOCK_MONOTONIC` time in nanoseconds.

### Negotiation

To use the extension, a source MUST issue `REG_SRC_NEGOTIATE` before
`REG_SRC_REGISTER`. The argument is a `reg_src_negotiate_args` (16
bytes):

| Field | Type | Description |
|---|---|---|
| `version` | `u32` | `REG_SRC_LIFETIME_VERSION`, which is 1. |
| `flags` | `u32` | Reserved. MUST be zero. |
| `session` | `u64` | MUST be zero on input. On success, the kernel writes a nonzero session identifier, unique to this open fd and never reused by a later fd. |

Any other version, nonzero flags or a nonzero input session fails
`EINVAL`. Negotiating after registration, or on a connection that is
closing, fails `EBUSY`.

### Request context

After reading a request and before responding to it, a negotiated source
MAY issue `REG_SRC_REQUEST_CONTEXT` with its session and the request's
id. The argument is a `reg_src_request_context_args` (40 bytes):

| Field | Type | Description |
|---|---|---|
| `session` | `u64` | The session returned by negotiation. |
| `request_id` | `u64` | The id of a request the source has read and not yet answered. |
| `request_deadline_ns` | `u64` | Output. When the kernel-side caller stops waiting, counting from when the request was queued. |
| `lifetime_deadline_ns` | `u64` | Output. The transaction's lifetime ceiling; zero for a transaction owned by one kernel operation, which has no separate ceiling. |
| `lease_deadline_ns` | `u64` | Output. The current cleanup lease; zero when the request has no live transaction owner. |

The context stays available after the kernel-side caller has given up,
until the source's response is accepted, so a source can still clean up
and answer a request it read late. A request the source has not read, or
has already answered, fails `ENOENT`.

### Renewing a lease

`REG_SRC_RENEW` takes a `reg_src_renew_args` (32 bytes): `session` and
`transaction_id` as inputs, and `lifetime_deadline_ns` and
`lease_deadline_ns` as outputs. On success the lease is extended to at
most five seconds from now, and never past the lifetime ceiling.

Renewal succeeds only for an existing transaction that has not ended,
whose kernel-side owner (a transaction fd, or a kernel operation) is
still live, on this source's own session. An unknown, released, expired
or foreign transaction fails `ESTALE`. A lease that has expired cannot
be renewed back to life. Releasing the last owner, or aborting the
transaction, ends renewal before the abort message is delivered.

None of the three ioctls uses an in-flight request slot, so a saturated
request queue cannot prevent renewal. On a connection that has not
negotiated, is not Active, or names another session, request context and
renewal fail `ESTALE`.

### What a negotiated source does with it

A source that negotiated:

- MUST stop holding transaction state (locks, an open storage
  transaction, a read snapshot) once that transaction's lease has
  expired or renewal has failed, and MUST treat the transaction as
  aborted from then on;
- MUST reject new operations on a transaction after its lifetime
  ceiling, and MUST serialize its rollback with the transaction's other
  operations and its commit;
- MUST report the true outcome of a commit it had already admitted when
  the lease or lifetime ran out, rather than inferring one from the
  expiry.

A lease is evidence that the kernel-side owner is alive. It is not an
inactivity timeout, and lease expiry does not change how the kernel
treats a commit response that arrives after its caller stopped waiting.
