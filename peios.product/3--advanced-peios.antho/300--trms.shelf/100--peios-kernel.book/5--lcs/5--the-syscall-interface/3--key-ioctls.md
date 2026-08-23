---
title: Key Ioctls
description: The sixteen ioctls acting on a key fd — reading, writing, security, watches, durability and bulk — each gated on the fd's granted mask.
---

Sixteen ioctls act on a key fd. Each checks the fd's granted mask
first and returns `EACCES` without contacting the source if the
required right is absent (§5.4.2). Numbers, directions and argument
layouts are in §5.A.

Every mutating ioctl accepts an optional transaction fd. So do the four
read ioctls — a read inside a bound transaction sees the transaction's
own uncommitted writes. A transaction bound to a different hive is
`EXDEV`; a committed, aborted or closed one is `EINVAL`; a timed-out
one is `ETIMEDOUT`; one whose source went Down is `EIO`. An unbound
transaction fd does not bind on a read, which is simply performed
non-transactionally.

Every mutating ioctl that names a layer performs layer write
authorization first (§5.3.4).

## Common errors

| Errno | Condition |
|---|---|
| `EACCES` | The granted mask lacks the required right, or layer write authorization failed. |
| `EFAULT` | An input pointer is invalid, or a non-zero-length output buffer pointer is null or unwritable. |
| `EIO` | The source is unavailable, failed, or the transaction's source went Down. |
| `ETIMEDOUT` | The source did not answer within `RequestTimeoutMs`, or the transaction had timed out. |
| `ENOMEM` | Kernel allocation failure. |
| `EXDEV` | The transaction is bound to a different hive. |
| `ENOENT` | The named layer is not in the layer table. |
| `EINVAL` | A non-zero reserved or padding field. |
| `ENOTTY` | An ioctl number this fd type does not implement. |

## Reading

**`REG_IOC_QUERY_VALUE`** returns the effective value at a name:
its type, data, the sequence number of the winning entry, and the
**canonical name of the winning layer** — which is the layer table's
spelling, not whatever string the source stored. A base-layer entry
therefore reports `base`. A winning tombstone or blanket, or no
entries at all, is `ENOENT`.

**`REG_IOC_QUERY_VALUES_BATCH`** returns every effective value on the
key in one call: name, type and data for each, with tombstoned and
blanket-masked values omitted. This is the call to use when you want
them all (§5.3.6).

**`REG_IOC_ENUM_VALUES`** and **`REG_IOC_ENUM_SUBKEYS`** return the
entry at an index, and `ENOENT` past the end. Both re-resolve the full
set on every call, and enumeration order is undefined — see §5.3.6 for
why the batch call usually wins.

`ENUM_SUBKEYS` performs no per-child access check. It returns every
visible child with its last write time, subkey count and value count.
The caller learns names and must open each child separately to read
anything (§5.4.2).

**`REG_IOC_QUERY_KEY_INFO`** returns the key's name, last write time,
subkey and value counts, the maximum subkey name length, maximum value
name length and maximum value data size, the descriptor size, the
volatile and symlink flags, and the hive generation number. It requires
`READ_CONTROL`.

It is declared `_IOR`, but it reads the caller's output-buffer fields
out of the argument structure before writing it back, so it is
read-write in practice.

### The hive generation number

A monotonic per-hive change epoch owned by the kernel. It is not a
sequence number and must not be read as one: sources neither report it
nor persist it (§5.3.7).

It is incremented once per committed mutation, or once per committed
transaction per affected hive, however many operations that transaction
contained. Its baseline is initialised from the source's reported
maximum sequence at registration so that observed values are monotonic
relative to persisted entries; saturating at `U64_MAX` is `EOVERFLOW`.

It is exposed on every key because it is cheap and because a watcher
that receives `OVERFLOW` can compare the generation it last saw with
the current one and skip the recovery re-read entirely if nothing has
committed (§5.6.4).

Layer operations produce a single generation increment covering the
metadata key deletion, `RSI_DELETE_LAYER`, the recomputation and the
resulting watch effects. There is no generation at which the metadata
key is gone but the layer's entries are still resolving. An operation
affecting several hives increments each independently.

## Writing

**`REG_IOC_SET_VALUE`** writes a value entry in a layer. LCS allocates
a sequence number and tells the source to store
`(key GUID, value name, layer) → (type, data, sequence)`, then updates
the key's last write time.

Writing type `REG_TOMBSTONE` is the explicit tombstone operation and
requires zero-length data (§5.2.6).

A non-zero `expected_sequence` makes the write **conditional**. It is
passed to the source, which atomically verifies that the layer's own
current entry carries that sequence number before writing, and answers
`RSI_CAS_FAILED` if not — which LCS returns as `EAGAIN`. There is no
kernel-side query-then-write: the check is the source's, and it is
atomic there or nowhere.

The condition is evaluated against the **layer's own entry**, not
against the effective value. A higher-precedence layer overriding a
value is not a lost update; it is the layer system working.

Additional errors: `EINVAL` for an unknown type or a tombstone with
data; `EAGAIN` for a failed conditional write; `ENOSPC` for the layer
cap or oversized data; `ENAMETOOLONG` for the value name; `EPERM` for a
`Precedence` above 0 without `SeTcbPrivilege` (§5.3.4).

**`REG_IOC_DELETE_VALUE`** removes one layer's entry at a value name —
whether that entry was a value or a tombstone. Removing a layer's
opinion lets lower-precedence layers surface.

The operation is meant to be idempotent, and it is idempotent as far as
a caller sees, provided the source answers `RSI_OK` for an entry that
was not there. LCS does not mask a source's `RSI_NOT_FOUND`; that
propagates as `ENOENT`. Idempotency is a source obligation, not a
kernel behaviour.

**`REG_IOC_BLANKET_TOMBSTONE`** sets or removes a blanket tombstone for
a layer on this key (§5.2.7). A new sequence number is assigned for
dispatch ordering, and watch events are generated for every value whose
effective state changed.

**`REG_IOC_DELETE_KEY`** removes this key's path entry from a layer.
The parent GUID comes from the fd's ancestor chain and the child name
from the last component of its resolved path. `ENOTEMPTY` if the key
has visible children; `EINVAL` on a hive root (§5.2.9).

**`REG_IOC_HIDE_KEY`** creates a HIDDEN path entry at the same place
instead, masking lower-precedence entries. The caller must hold an open
fd to the key, which is how it proved access to it. `EINVAL` on a hive
root.

## Security

**`REG_IOC_GET_SECURITY`** and **`REG_IOC_SET_SECURITY`** read and
merge Security Descriptor components, selected by a `security_info`
bitmask. §5.4.3 covers the rights, the merge, and the validation.

## Watches, durability, bulk

**`REG_IOC_NOTIFY`** arms, re-arms or disarms a watch (§5.6.1).

**`REG_IOC_FLUSH`** tells the source to persist pending writes for this
key's hive, and returns when persistence is confirmed. The hive name
comes from the first component of the fd's resolved path. It requires
`KEY_SET_VALUE` (§5.4.2).

**`REG_IOC_BACKUP`** and **`REG_IOC_RESTORE`** export and replace a
subtree. They are privilege-gated with no per-key access check, and
they are covered in §5.9.
