---
title: Keys and image build
type: concept
description: The public-key catalog compiled into the kernel, the TCB private key held only by the release infrastructure, and how a signature gets from pekit onto the filesystem.
related:
  - peios/binary-signing/overview
  - peios/binary-signing/signature-format
  - peios/binary-signing/verification-and-pinning
  - peios/process-integrity-protection/overview
---

A signed binary's trust level is whatever the **key that signed it** says it should be. The mapping from "this key" to "this PIP level" is the kernel's public-key catalog. The catalog is compiled into the kernel image; there is no way to add keys to a running system, and there is no way to remove them either short of replacing the kernel.

This page covers the catalog's structure, who holds the private keys, how `pekit` uses them and how `peipkg` carries the result onto disk, the constraints on key handling, and the v0.20 limitation of having only one key.

## The catalog

The kernel holds an in-memory table mapping each known public key to the PIP level its signature confers. Each entry is structured:

| Field | Size | Meaning |
|---|---|---|
| Public key | 1952 bytes | The raw ML-DSA-65 public key. |
| `pip_type` | 4 bytes (little-endian u32) | The PIP type this key represents. |
| `pip_trust` | 4 bytes (little-endian u32) | The PIP trust level this key represents. |

Each entry is 1960 bytes. The table is a contiguous array of entries terminated by an all-zero entry — the kernel walks until it sees a sentinel.

At exec, when the kernel verifies a signature, it tries each key in the table in turn until one verifies the signature or the table runs out. If a key verifies, its `pip_type` and `pip_trust` are written to the new process's PSB. If no key verifies, the binary is treated as unsigned.

The table is part of the kernel image. It is read-only at runtime; there is no syscall to add an entry, modify an entry, or remove one. Replacing the table requires replacing the kernel.

### Why ML-DSA-65

FIPS 204 defines three parameter sets — ML-DSA-44, ML-DSA-65 and ML-DSA-87 — trading signature size against security margin. Peios uses **ML-DSA-65**, and the deciding constraint is where signatures live rather than cryptographic preference.

Non-ELF files carry their signature in the `security.peios.sig` extended attribute. Most ext4-family filesystems cap an xattr value at one filesystem block, typically 4096 bytes, unless the large-xattr (`ea_inode`) feature is enabled. ML-DSA-65's 3310-byte blob fits inside that with room to spare; ML-DSA-87's would be 4628 bytes and would not fit. ML-DSA-44 would fit too, but saves under a kilobyte per signature in exchange for a smaller security margin — a poor trade for an OS expected to have a long life.

So ML-DSA-65 is the largest parameter set that keeps signatures storable as ordinary extended attributes on ordinary filesystems.

## What v0.20 actually contains

In v0.20, the catalog has **one entry**: the **TCB key**. The mapping is:

| Key | `pip_type` | `pip_trust` | What it represents |
|---|---|---|---|
| TCB public key | 512 (Protected) | 8192 | Peios TCB binaries — peinit, authd, loregd, lpsd, eventd |

That is it. No App-level key, no Authenticode key, no AntiMalware key. The categorical PIP labels described in [Process integrity protection](~peios/process-integrity-protection/overview) — Protected/1024 for Authenticode, Protected/1536 for AntiMalware, Protected/2048 for App, Protected/4096 for Peios — are *defined* in the model but no key in v0.20 corresponds to them. No binary on a v0.20 system will have these PIP values because nothing exists to sign them at those levels.

The implication: every signed binary on a v0.20 Peios system runs at PIP Protected/8192. There are no other PIP-protected processes. PIP is binary: a process is either TCB-level or unprotected.

Future Peios versions will add keys for the other tiers. App-level signing will let Peios-distributed applications get their own PIP protection (mid-trust); Authenticode-level will let third-party signed binaries run at low-but-non-zero trust; AntiMalware-level will protect security tooling. The catalog grows; the model accommodates it without code changes.

## The TCB private key

The TCB **private key** is what `pekit` uses to sign TCB binaries and firmware when their packages are built. It is the most security-sensitive artefact in the entire system: anyone with the TCB private key can sign a binary that the kernel will then trust at the highest level. There is no revocation, no per-binary blocklist, no way to invalidate a signed binary short of removing it.

> [!CAUTION]
> **The TCB private key must never be present on any running Peios system.** It is for image build, and only image build. A running system has no need for the private key — the kernel verifies with the public key only.

The other constraints on the private key are just as absolute:

- **The key is held by whoever builds the system image** (in practice, the Peios project's release infrastructure for the official distribution; potentially a downstream packager for a fork).
- **The key is not distributed.** Users do not get a copy of the private key. They get the binaries the private key was used to sign.

The standard pattern: build infrastructure with the private key produces image artefacts. The artefacts include the public key compiled into the kernel image and the signed TCB binaries. The artefacts ship; the private key stays in the build infrastructure.

A system whose private key has been compromised loses the security guarantees of PIP. There is no way to retroactively recover from such a compromise; the only fix is to release a new image with a new public key and re-sign all TCB binaries with the new private key, then deploy. Existing systems running the old image continue to trust the old key.

## pekit, peipkg and the build flow

Signing happens when a package is built, not when an image is assembled. `pekit`, the package builder, holds the TCB private key on the release infrastructure and signs as part of packing; `peipkg` and `peipkg-compose` (which `peiso` drives to lay down the image's root) carry the result onto the filesystem. No step in between needs the private key.

At package build, for each file a recipe's `sign.pip` table names, pekit:

1. Computes the content hash — ELF section zeroed for an ELF file, the entire file for anything else (see [Signature format](~peios/binary-signing/signature-format)).
2. Signs the hash with the TCB private key and builds the 3310-byte blob (version byte + ML-DSA-65 signature).
3. Places the blob. For an ELF file it reserves the `.peios.sig` section (3310 zero bytes) *before* hashing and writes the blob into it afterwards, so the hash the kernel computes matches the one signed. For a non-ELF file — a firmware blob, a data file — it writes the blob as a **detached signature**, `<file>.peios.sig`, next to the file. The file itself is untouched.
4. Packs both into the `.peipkg`. The detached signature is an ordinary payload entry with a reserved suffix; the package format forbids extended attributes on entries, so this is how the xattr placement travels.

At install — whether `peipkg install` on a running system or `peipkg-compose` building an image root — for each detached signature the installer creates the target file, sets `security.peios.sig` on it to the blob's bytes, and does not write the detached entry to disk at all. The signature is checked at pack time for shape (right length, right version byte, a target that exists and is not ELF); the installer never needs a key.

When the image boots, the kernel's embedded key table verifies binaries from their sections and firmware and other non-ELF content from their xattrs. No private key is involved at runtime.

## Why one key in v0.20

A reasonable question: why does v0.20 ship with only the TCB key? Why not at least an App key for Peios-distributed applications?

The answer is that the App, Authenticode, and AntiMalware tiers require infrastructure that v0.20 does not have:

- **App-level signing** requires a Peios-managed signing service that signs released applications. The service exists conceptually; the operational pipeline does not.
- **Authenticode-level signing** requires a trust agreement with one or more third-party CAs or a Peios-managed equivalent. None of that is in place.
- **AntiMalware** requires a vetting process for security-tooling vendors. Same status.

The TCB key, by contrast, is just the project's own key, used to sign the project's own binaries. The infrastructure is the project's own release pipeline. It works on day one.

Future Peios versions will add the other tiers as the corresponding infrastructure comes online. The model accommodates them. The catalog grows. Until then, the only PIP-protected processes are TCB processes, and the model effectively has two levels: TCB and not-TCB.

## Implications for ordinary deployments

For someone running Peios:

- **No signing tools are available on a running system.** You cannot sign your own binaries to get PIP protection. The TCB private key is not available; no other key is defined.
- **Binaries you write or compile yourself run as `pip_type = None`.** Including binaries built from source on the running Peios system. This is correct behaviour — there is no path for an untrusted-by-the-OS binary to acquire trust.
- **The only PIP-protected processes are TCB.** peinit, authd, loregd, lpsd, eventd, and that is it. Everything else runs at None.
- **Updates to TCB binaries come through the package system.** A new release of authd, say, is in a `.peipkg` signed by the project's package-signing infrastructure (separate from the TCB binary signing — packages have their own signature for distribution integrity). The binary inside the package carries the TCB-key signature for PIP. Installing the package places the binary on disk; the kernel verifies it at next exec.

For administrators of a custom Peios fork (using their own kernel image with their own key catalog), the same model applies with whatever keys they have defined: their TCB-equivalent key signs their TCB binaries, those binaries run at TCB-equivalent PIP, and nothing else has PIP protection unless they add keys to their catalog.

## Where to go next

For the enforcement flow these keys feed — verification at exec and inode pinning — read [Verification and pinning](~peios/binary-signing/verification-and-pinning).

For the per-process hardening flags that build on signing — LSV gates executable mappings by signature trust — read [Process mitigations](~peios/process-mitigations/overview).
