---
title: Conformance
description: The status vocabulary, the obligations not tied to one operation, what the kernel validates, and where the trust boundary falls.
---

A conforming source MUST satisfy every requirement in this chapter.
This section collects the obligations that are not tied to one
operation, and the status vocabulary.

## Status codes

Every response payload begins with a `u32` status. Zero is success.

| Status | Code | Kernel maps to | Meaning |
|---|---|---|---|
| `RSI_OK` | 0 | success | The operation completed. |
| `RSI_NOT_FOUND` | 1 | `ENOENT` | A key, value or path entry does not exist. |
| `RSI_ALREADY_EXISTS` | 2 | `EEXIST` | A path entry or key already exists. |
| `RSI_STORAGE_ERROR` | 3 | `EIO` | A failure in the backing store. |
| `RSI_NOT_EMPTY` | 4 | `ENOTEMPTY` | A key still has children or values. |
| `RSI_TOO_LARGE` | 5 | `ENOSPC` | Value data exceeds the maximum size. |
| `RSI_TXN_BUSY` | 6 | `EBUSY` | A transaction could not take the write lock. |
| `RSI_INVALID` | 7 | `EINVAL` | A malformed request or an invalid field value. |
| `RSI_CAS_FAILED` | 8 | `EAGAIN` | A conditional write's sequence did not match. |
| `RSI_TXN_NOT_SUPPORTED` | 9 | `ENOTSUP` | This transaction mode is not supported. |

A source MUST NOT return a code outside this vocabulary. One outside it
is malformed data.

Source-specific detail is never surfaced to the process that made the
registry call. The status is the whole interface, and a source MUST
choose the code that most accurately describes what happened.

## Obligations

**Respond to everything.** A source MUST send exactly one response for
every request it has read, even after the kernel-side caller has timed
out. A request the source has read and will never answer occupies an
in-flight slot until the connection is torn down.

**Return complete layer data.** When asked for values or path entries,
a source MUST return **all** layer entries. It MUST NOT pre-filter,
resolve, or omit any. Layer resolution is the kernel's.

**Order enumerations deterministically.** The same request against
unchanged hive state MUST return the same ordering every time. This
applies to the child list of `RSI_ENUM_CHILDREN`, the value entries and
the blanket tombstone list of `RSI_QUERY_VALUES`, and the path entries
of `RSI_LOOKUP`. Ascending folded name, then layer, then sequence
satisfies it.

This is correctness, not tidiness. The kernel exposes enumeration to
callers as a dense index walk — position 0, 1, 2 until exhaustion —
observing the source's ordering at each step. A source that returns the
same set in a different order across those observations makes the walk
revisit some entries and never see others, which surfaces as duplicate
and silently missing keys. An unordered SQL query or a hash-map
iteration does **not** satisfy this: `UNION ALL` without `ORDER BY` and
deliberately randomised map iteration both yield different orderings
for identical input.

The obligation constrains ordering **within one response** only. It
does not constrain the order in which concurrent requests are
processed, and it does not by itself make a multi-step enumeration
atomic against concurrent mutation — a caller that needs a stable view
across a whole walk uses a read-only transaction.

**Preserve GUIDs exactly.** A source MUST persist a GUID as given.

**Handle concurrency.** A source MUST handle multiple in-flight
requests without head-of-line blocking, and MAY process them in any
order.

**Serialise commits.** Concurrent read-write commits MUST be
serialised, and a commit MUST be atomic. The kernel does no conflict
detection: it relies on commits being ordered and atomic, and lets the
later write win by sequence number.

**Support conditional writes.** `expected_sequence` on `RSI_SET_VALUE`
MUST be honoured atomically.

**Protect immutable fields.** `RSI_WRITE_KEY` requests attempting to
modify the GUID, the volatile flag or the symlink flag MUST be rejected
with `RSI_INVALID`.

**Create hive roots on first boot**, and **purge orphans before
registering**. Both are described in §4.2.

## What the kernel validates

A source cannot rely on a malformed response being tolerated. The
kernel checks each of the following, and two categories of failure have
different consequences.

**Malformed data** — a structurally valid message with invalid content
— fails the request with `EIO`, emits an audit event naming the source
and the class of failure, and **leaves the source running**, since
corruption may be localised. The classes are: an unparseable or
mask-invalid Security Descriptor; an invalid layer name, key name or
value name; a payload of the wrong shape or with trailing bytes; a
metadata block that is incomplete, duplicated, unreferenced or nil; an
invalid value type, a tombstone carrying data, or oversized data; a
nil or duplicated orphan GUID; a status code outside the vocabulary;
and the two sequence rules below.

**Malformed protocol** — a structurally invalid message, a framing
error, an unknown or duplicate request id, an operation code that does
not match its request — is treated as a crash. The connection is torn
down and the source is marked Down.

### The two sequence rules

A source MUST NOT return a layer-qualified entry whose sequence number
is greater than or equal to the next number the kernel would allocate.
Sources store the numbers the kernel assigns them and cannot
legitimately hold a future one. Without this rule a compromised source
could fabricate a sequence number and win every resolution tie in its
own hives.

A source MUST NOT return duplicate sequence numbers at the same
precedence where they would have to be compared to select a winner.
The kernel rejects the response rather than choosing arbitrarily.
Duplicates that are never compared are not an error.

## The trust boundary

A source is inside the trusted computing base. The kernel has no
independent copy of anything a source returns, so a compromised source
controls the access-control outcome for its hives entirely: it can
return a permissive Security Descriptor for any key and the kernel will
enforce it. Structural validation catches malformed data; it cannot
catch data that is well-formed and false.

Three consequences follow that an operator should understand.

A source backing the hive that holds layer metadata can fabricate
precedence and enabled values, and so decide which layer wins every
resolution contest system-wide. The privilege check applied when
precedence is *written* does nothing about a fabricated *read*.

The same source can return permissive descriptors for layer metadata
keys, granting any process write access to any layer.

`SeRestorePrivilege` implies descriptor control: a restore replaces
every Security Descriptor in the subtree it covers.

Sources MUST therefore run with tightly scoped privileges and be
protected by descriptors on their service definitions. The kernel emits
an audit event for every source data validation failure.
