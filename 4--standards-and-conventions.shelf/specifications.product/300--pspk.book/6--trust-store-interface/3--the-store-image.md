---
title: The Store Image
description: The layout of the store image at /system/pso/store, when the
  kernel reads it, how it decides whether each top-level is rooted, and
  what happens when the image is missing or damaged.
---

The **store image** is one file, `/system/pso/store`, holding every
object of the store.

| Field | Type | Description |
|---|---|---|
| header | 6 bytes | The header of PGSS §7.4, with `kind` `0x06` |
| `count` | `u32` | The number of entries |
| entries | Variable | `count` entries, each a `u16` length and an object |

An entry's object is one of:

- a certificate whose role is top-level (PGSS §7.6)
- a revocation (PGSS §7.12)
- a distrust entry (PGSS §7.13)

Entries are in no required order, and an object that appears twice
counts once. The image is not signed.

## When the kernel reads it

The kernel reads the image once, from the root filesystem it has when
it is about to run its first program, and before it runs that program.
On a system that boots through an initramfs, that is the initramfs, so
the image has to be in it (PSPU §5.28).

The kernel MUST NOT read the image again. Every later change arrives
through ktrust (§6.5).

## How the kernel treats each top-level

For each top-level, in the image or added later, the kernel reads the
`issuer` field and does one of three things:

- **The issuer is the key hash of a root the kernel holds.** The kernel
  verifies the signature under that root. If it verifies, the top-level
  is enabled and rooted. If it does not, the kernel rejects the entry.
- **The issuer is the key hash of the certificate's own key.** The
  kernel verifies the signature under that key. If it verifies, the
  top-level is enabled and unrooted. If it does not, the kernel rejects
  the entry.
- **The issuer is anything else.** The kernel has no key to check the
  signature with. The top-level is enabled and unrooted.

A store keeper never tells the kernel which of these applies. The
kernel decides from the certificate alone.

> [!NOTE]
> A flag saying "this one is rooted" would be one more thing the
> kernel had to believe, on the one question a signature can answer
> outright.

## A missing or damaged image

If the image is absent, the store starts empty.

If the image is malformed as a whole, with a bad header, a length that
runs past the end of the file, or bytes after the last entry, the kernel
MUST treat the store as empty and MUST report the failure.

If a single entry is malformed, is of a kind the image does not hold,
or is rejected as this article describes, the kernel MUST skip that
entry, keep the rest, and report it.

An empty store enables no top-level, so no chain is rooted. Where the
kernel requires a rooted chain to run its first program, a system with
a missing or damaged image does not boot, and is repaired from outside.

## Writing the image

A store keeper MUST write the image whenever the store changes, and
MUST replace it in one step, so that a reader never finds a partial
file.

The image a kernel reads at boot can be older than the store on disk,
because an initramfs is built ahead of time. A store keeper MUST bring
the kernel up to date when it attaches (§6.5).

> [!NOTE]
> The image depends on the protection of the file for everything a
> signature does not cover: which unrooted top-levels are in it, and
> which distrust entries. A party able to alter boot files can alter
> those. Root-signed top-levels and revocations prove themselves and
> cannot be forged this way, only left out.
