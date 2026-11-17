---
title: Operations
description: The five ktrust ioctls for adding, removing, and listing
  store objects and for listing and fetching seen certificates, their
  argument structures, their errors, and how a store keeper reconciles
  after attaching.
---

A store keeper issues every operation as an ioctl on the device
descriptor. Each takes a pointer to one structure. Reserved fields MUST
be zero, and the kernel fails `EINVAL` if one is not.

| Ioctl | Purpose |
|---|---|
| `KTRUST_ADD` | Add one object to the store |
| `KTRUST_REMOVE` | Remove one object from the store |
| `KTRUST_LIST` | List the objects of one kind |
| `KTRUST_SEEN_LIST` | List the seen certificates |
| `KTRUST_SEEN_GET` | Fetch one seen certificate |

## Generation

The kernel holds a `u64` generation, which starts at 1 once the store
image is read and rises by one for each `KTRUST_ADD` or `KTRUST_REMOVE`
that changes the store. Every operation that reads or changes the
store returns the generation as it stands when the operation
completes.

## KTRUST_ADD

The argument is a `ktrust_add_args`.

| Field | Type | Description |
|---|---|---|
| `object_ptr` | `u64` | Address of the object |
| `object_len` | `u32` | Length of the object |
| `_pad` | `u32` | Reserved |
| `generation` | `u64` | Out: the generation |

The object is a top-level certificate, a revocation, or a distrust
entry. The kernel treats it exactly as it treats an entry of the store
image (§6.3).

Adding an object the store already holds succeeds and changes nothing.

| Error | Meaning |
|---|---|
| `EINVAL` | The object is malformed, or is not one of the three kinds |
| `EKEYREJECTED` | A top-level's signature does not verify |
| `ENOSPC` | The store is at a limit (§6.A) |

The kernel does not require proof that a revocation applies to
anything. It keeps the revocation and applies it to a chain when
PGSS §7.12 says it applies. Showing that a revocation is worth keeping
is the store keeper's (PGSS §7.12).

## KTRUST_REMOVE

The argument is a `ktrust_remove_args`.

| Field | Type | Description |
|---|---|---|
| `kind` | `u8` | `0x01` for a top-level, `0x05` for a distrust entry |
| `_pad` | `u8[7]` | Reserved |
| `hash` | `u8[64]` | The top-level's object hash, or the hash a distrust entry distrusts |
| `generation` | `u64` | Out: the generation |

| Error | Meaning |
|---|---|
| `EINVAL` | `kind` is neither value |
| `EPERM` | `kind` is `0x04`: a revocation is never removed |
| `ENOENT` | The store holds no such object |

## KTRUST_LIST

The argument is a `ktrust_list_args`.

| Field | Type | Description |
|---|---|---|
| `kind` | `u8` | `0x01`, `0x04`, or `0x05` |
| `_pad` | `u8[7]` | Reserved |
| `cursor` | `u64` | In: 0 to start, or the value last returned. Out: the value to continue with |
| `buf_ptr` | `u64` | Address of a buffer for entries |
| `buf_len` | `u32` | Length of the buffer |
| `count` | `u32` | Out: the number of entries written |
| `generation` | `u64` | Out: the generation |

The kernel writes whole `ktrust_entry` structures, as many as fit. A
`count` of 0 means the list is complete.

| Field | Type | Description |
|---|---|---|
| `hash` | `u8[64]` | A top-level's or revocation's object hash, or the hash a distrust entry distrusts |
| `detail` | `u8` | For a top-level, `0x01` rooted or `0x02` unrooted. Otherwise the entry's `target_type` |
| `_pad` | `u8[7]` | Reserved |

If the generation changes between two calls of one listing, the
listing might repeat or miss an entry. A store keeper that needs a
consistent view MUST start again.

## KTRUST_SEEN_LIST

The kernel records every certificate it verifies as part of a chain,
whether the certificate came from a bundle, from a directory of
intermediaries, or from the store. The record lasts until the system
restarts. Leaves are not recorded.

The argument is a `ktrust_seen_list_args`.

| Field | Type | Description |
|---|---|---|
| `cursor` | `u64` | As for `KTRUST_LIST` |
| `buf_ptr` | `u64` | Address of a buffer for entries |
| `buf_len` | `u32` | Length of the buffer |
| `count` | `u32` | Out: the number of entries written |

Each entry is a `ktrust_seen_entry`.

| Field | Type | Description |
|---|---|---|
| `hash` | `u8[64]` | The certificate's object hash |
| `issuer` | `u8[64]` | The certificate's `issuer` field |
| `top_level` | `u8[64]` | The object hash of the top-level it was last verified under |
| `use_count` | `u64` | Verifications that passed through it |
| `first_seen` | `u64` | Nanoseconds since boot at the first |
| `last_seen` | `u64` | Nanoseconds since boot at the most recent |
| `live` | `u32` | Processes running under a chain that passes through it |
| `_pad` | `u32` | Reserved |

## KTRUST_SEEN_GET

The argument is a `ktrust_seen_get_args`.

| Field | Type | Description |
|---|---|---|
| `hash` | `u8[64]` | The certificate's object hash |
| `buf_ptr` | `u64` | Address of a buffer for the certificate |
| `buf_len` | `u32` | Length of the buffer |
| `object_len` | `u32` | Out: the certificate's length |

| Error | Meaning |
|---|---|
| `ENOENT` | No such certificate has been seen |
| `ERANGE` | The buffer is too small. `object_len` holds the length needed |

## Reconciling after attaching

The kernel's store at the moment a store keeper attaches is whatever
the image held at boot, plus whatever earlier store keepers added. A
store keeper MUST then make it match the trust store it reads from
disk:

1. List each kind.
2. Add every top-level, revocation, and distrust entry the trust store
   holds and the kernel does not.
3. Remove every top-level and distrust entry the kernel holds and the
   trust store does not.

A store keeper MUST NOT treat a revocation the kernel holds and the
trust store does not as an error. It adds that revocation to the trust
store (PGSS §7.12).
