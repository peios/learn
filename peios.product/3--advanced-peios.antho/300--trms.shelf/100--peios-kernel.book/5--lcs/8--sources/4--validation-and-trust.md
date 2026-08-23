---
title: Validation
description: LCS validates every response before using it — malformed data against malformed protocol, and the asymmetric extensibility between them.
---

LCS validates every response before using it, and the failures split
into two categories with very different consequences.

## Malformed data

The RSI message is structurally valid but its content is not: a
descriptor that will not parse, a value type that does not exist, a
sequence number that cannot be real, a metadata block that does not
cover the GUIDs it should.

- The request returns `EIO` to its caller.
- An `LCS_SOURCE_VALIDATION_FAILURE` audit event is emitted, naming the
  source slot and — where known — the hive, the request id, the
  operation code, the key GUID, and which of the twelve validation
  classes applies (§5.4.4).
- **The source stays alive.** Corruption may be localised, and one bad
  key is not a reason to take a hive offline.

What is checked, by category:

- **Security Descriptors**, from lookups and from layer metadata
  refreshes, must parse and must satisfy the ACE mask rules of §5.4.2.
  A malformed layer metadata descriptor additionally leaves the
  previous known-good one cached (§5.3.3).
- **Names** — layer names, key and child names, value names — must be
  valid under the ordinary rules for their kind.
- **Sequence numbers** must be below the next number LCS would
  allocate, and must not duplicate at the same precedence in a way that
  would decide a winner (§5.3.6).
- **Payload shape** — an otherwise-matched response whose
  operation-specific payload is the wrong shape, carries trailing
  bytes, or encodes a path target invalidly.
- **Metadata closure** — a lookup or enumeration whose per-GUID
  metadata block has missing, duplicate, unreferenced or nil entries.
  A HIDDEN entry must carry an all-zero GUID and contributes no
  metadata.
- **Value payloads** — invalid types, a tombstone carrying data, data
  above `MaxValueSize`.
- **Orphan lists** — a nil or duplicated GUID in an `RSI_DELETE_LAYER`
  response.
- **Status codes** outside the defined vocabulary.

## Malformed protocol

The message itself is structurally invalid: bad framing, a truncated
response, an unknown request id, a duplicate response, an operation
code that does not match the request.

This is treated as a source crash. The connection is torn down, the
in-flight table is destroyed with every waiter completed `EIO`, the
slot is marked Down, its hives become unavailable, and bound
transactions enter `SOURCE_DOWN`.

There is one case where malformed *data* also takes the source down:
when the caller had already timed out and the operation was a commit or
a replayable mutation. At that point LCS cannot establish whether a
mutation was applied, and it cannot account for one it cannot describe
(§5.8.5).

## Asymmetric extensibility

Requests and responses do not extend the same way.

A **request** may carry trailing fields a source does not recognise; a
source skips them using `total_len`. That is how a new optional field
is added without an RSI version bump.

A **response** may not. LCS rejects any trailing bytes in a response
payload as malformed data. Forward compatibility on the response side
comes from new operations, not from extending existing payloads.
