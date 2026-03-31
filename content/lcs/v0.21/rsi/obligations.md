---
title: Source Obligations
order: 3
---

A conforming source MUST satisfy all obligations in this section.

## Response timeliness

A source MUST respond to every request. LCS enforces
RequestTimeoutMs (default 30 seconds). Unresponsive sources cause
ETIMEDOUT for waiting threads. The source is not disconnected on
timeout -- it remains active and late responses are processed
normally.

## Complete layer data

When asked for values or path entries, a source MUST return ALL
layer entries. Sources MUST NOT pre-filter, resolve, or omit
entries. Layer resolution is LCS's responsibility.

## GUID fidelity

GUIDs are assigned by LCS and passed to the source for storage.
Sources MUST persist GUIDs exactly as given. No rewriting, no
remapping, no reassignment.

## Concurrency

RSI is multiplexed. A source MUST handle multiple in-flight
requests without head-of-line blocking. Sources MAY process
requests in any order.

## Transaction support

Sources MUST support the transaction operations
(RSI_BEGIN_TRANSACTION, RSI_COMMIT_TRANSACTION,
RSI_ABORT_TRANSACTION). Commits MUST be atomic (all-or-nothing).
Concurrent commits MUST be serialised.

Sources whose backing store does not support transactions MAY treat
each operation as auto-committed and return RSI_TXN_NOT_SUPPORTED
for explicit transaction requests. LCS maps this to ENOTSUP for
the calling thread.

## Conditional write support

Sources MUST support the expected_sequence field on RSI_SET_VALUE.
When expected_sequence is non-zero, the source MUST atomically
verify the current entry's sequence number matches before writing.
If the condition fails, the source MUST return RSI_CAS_FAILED
without writing.

## Hive root creation

On first boot (empty database), sources MUST create root key
records for each hive they back. The source generates random GUIDs
for hive roots, creates the key records with appropriate default
SDs (see the Hive Root SDs section in security/access-control.md),
and persists them. The root GUIDs are provided to LCS in the
REG_SRC_REGISTER handshake. Subsequent startups use the persisted
root GUIDs.

## Crash recovery

On startup, sources MUST clean up orphaned GUIDs before completing
registration with LCS. An orphaned GUID is a key record with no
path entries in any layer. Sources MUST query for and purge these
records as part of their initialisation sequence.

## Immutable field protection

Sources MUST reject RSI_WRITE_KEY requests that attempt to modify
immutable fields (GUID, volatile flag, symlink flag). Return
RSI_INVALID.

## Source errors

Sources report errors via a status code in the response message.
LCS maps these to errnos.

| Source error | Code | Mapped errno | Meaning |
|---|---|---|---|
| RSI_OK | 0 | (success) | Operation completed. |
| RSI_NOT_FOUND | 1 | ENOENT | Key, value, or path entry does not exist. |
| RSI_ALREADY_EXISTS | 2 | EEXIST | Path entry or key already exists. |
| RSI_STORAGE_ERROR | 3 | EIO | Backing store I/O failure. |
| RSI_NOT_EMPTY | 4 | ENOTEMPTY | Cannot drop a key that still has children or values. |
| RSI_TOO_LARGE | 5 | ENOSPC | Value data exceeds maximum size. |
| RSI_TXN_BUSY | 6 | EBUSY | Transaction could not acquire write lock. |
| RSI_INVALID | 7 | EINVAL | Malformed request or invalid field value. |
| RSI_CAS_FAILED | 8 | EAGAIN | Conditional write failed -- sequence mismatch. |
| RSI_TXN_NOT_SUPPORTED | 9 | ENOTSUP | Source does not support explicit transactions. |

## Data validation by LCS

LCS validates every response from a source:

**Malformed data** (structurally valid RSI response, but invalid
content -- SD that doesn't parse, impossible field values):

- Request returns EIO to the caller.
- LCS emits an audit event identifying the source, key GUID, and
  nature of the validation failure.
- Source stays alive. Corruption may be localised.

**Sequence number validation.** LCS MUST reject any entry in an
RSI response whose sequence number exceeds the current global
sequence counter. Such entries are treated as malformed data (EIO
+ audit event). This prevents a compromised source from
fabricating sequence numbers to win layer resolution tiebreaks.

The same structural SD validation applies to layer metadata SDs
loaded during layer table cache refresh. A malformed SD on a layer
metadata key produces an audit event and the layer's cached SD is
not updated (the previous known-good SD is retained).

**Malformed protocol** (RSI message itself is structurally invalid
-- framing errors, unknown message types, truncated responses):

- Treated as a source crash. Connection torn down, hives marked
  unavailable.
- A source that cannot speak the protocol is fundamentally
  untrustworthy.

## Trust boundary

Sources are in the TCB. A compromised source has full control over
the access control outcome for its hives: it can return a
permissive SD for any key, causing AccessCheck to grant access that
should be denied. LCS validates structural correctness of source
responses (malformed SDs produce EIO) but cannot detect
semantically incorrect but well-formed data (e.g., an SD that
grants Everyone KEY_ALL_ACCESS on a sensitive key).

Mitigations:

- Sources MUST run with tightly scoped privileges and be protected
  by SDs on their service definitions.
- LCS MUST emit audit events for source data validation failures.
- Source processes are critical-path components managed by peinit
  with PIP (Process Integrity Protection) where available.
- A future hardening path could involve LCS checksumming SDs it
  computes during inheritance and verifying them on retrieval, but
  this is not a v0.21 requirement.

Specific high-impact consequences of source compromise:

- **Layer table poisoning.** A compromised source can return
  fabricated precedence or enabled values for layer metadata
  under `Machine\System\Registry\Layers\`, effectively
  controlling which layer wins every resolution contest
  system-wide. The SeTcbPrivilege check at write time does not
  protect against read-path fabrication.

- **Layer write authorization bypass.** A compromised source can
  return permissive SDs for layer metadata keys, granting any
  process write access to any layer via the layer write
  authorization check.

- **SeRestorePrivilege scope.** SeRestorePrivilege effectively
  confers WRITE_DAC and WRITE_OWNER on any key in the restore
  subtree, because restore replaces the entire subtree including
  SDs. Operators granting SeRestorePrivilege should understand
  it implies full SD modification capability.

## Forward compatibility

The RSI uses a versioned, extensible message format. New optional
fields can be appended to requests without breaking existing
sources. Sources MUST ignore fields they do not recognise (the
total_len field allows skipping unknown trailing data). This
enables future features to be added without RSI version bumps.
