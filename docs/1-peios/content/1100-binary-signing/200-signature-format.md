---
title: Signature format
type: concept
description: A Peios signature is 65 bytes — a version byte plus a 64-byte Ed25519 signature over a 32-byte SHA-256 hash. The same blob lives in different places depending on the file type. This page covers the format itself, where it goes for ELF and non-ELF files, and how the hash is computed in each case.
related:
  - peios/binary-signing/overview
  - peios/binary-signing/verification-and-pinning
  - peios/binary-signing/keys-and-image-build
---

The signature blob is the same shape regardless of where it sits — sixty-five bytes, structured as a version byte followed by an Ed25519 signature. What changes is where the blob lives and what bytes it covers. ELF binaries hold the blob in a dedicated section; non-ELF executables hold it in an extended attribute or alongside the file. The hash being signed is computed differently for each.

This page covers the blob's structure, where it can live, and how the content hash is computed for each placement.

## The signature blob

Every Peios signature is exactly **65 bytes**:

| Bytes | Field | Meaning |
|---|---|---|
| 0 | Version | `0x01`. The only version supported in v0.20; any other value is rejected. |
| 1–64 | Ed25519 signature | A 64-byte raw Ed25519 signature. The thing the kernel verifies. |

The version byte is what gives the kernel room to evolve the format. A signature with version `0x02` (for example) would be treated as unrecognised in v0.20 — the kernel does not panic, it just declines to verify the signature, and the process runs at `pip_type = None`. Future versions may define new layouts; current versions will see them as if they were absent.

The Ed25519 signature is computed over a 32-byte content hash (covered below), using standard Ed25519 — **not** Ed25519ph. The pre-hash variant Ed25519ph is for cases where the message is hashed first by the signer; here the kernel signs a 32-byte hash as if it were the message itself. The hash is what is hashed-and-signed inside the Ed25519 algorithm; there is no double-hashing.

The 64-byte signature is the raw `(R || S)` pair Ed25519 produces — no encoding, no envelope, no metadata. The kernel parses it as raw bytes and feeds them straight into the verification routine.

## Where the blob lives

A signature blob can live in three places, depending on the file:

| Placement | When used |
|---|---|
| ELF section `.peios.sig` | ELF binaries. The signature lives inside the file. |
| `security.peios.sig` xattr | Non-ELF binaries. Also a fallback for ELF binaries without a `.peios.sig` section. |
| Detached `.sig` file | Used during image build for non-ELF executables. The image builder reads the detached file and stamps the xattr. |

The order matters. For ELF binaries the kernel looks for the `.peios.sig` section first; if found, the xattr is **not** consulted as a fallback. The ELF section is the canonical location.

For non-ELF binaries — scripts (which are themselves not signed; see [Verification and pinning](~peios/binary-signing/verification-and-pinning)), data files used by tools, anything that does not begin with the ELF magic — only the xattr is consulted.

Detached `.sig` files are a transient form. They exist on the file system being assembled by `peiso` (the image builder) so that the builder can stamp the xattr from them. By the time the image boots, detached files are not used; the xattrs are what the kernel reads.

### The ELF `.peios.sig` section

For ELF binaries, the signature lives in a section of the binary's own ELF structure:

| Attribute | Value |
|---|---|
| Section name | `.peios.sig` |
| Section type | `SHT_PROGBITS` (typical ELF section type, holds raw data) |
| Section size | Exactly 65 bytes |

The section is part of the ELF file. It travels with the binary through every operation a normal ELF travels through: filesystem copy, network transfer, package archive, image-build, anything. As long as the ELF is intact, the signature is part of it.

This is why the ELF section is preferred for ELF binaries. An xattr is filesystem metadata; it can be lost in a copy that does not preserve xattrs (a `cp` without `--preserve=xattr`, an archiver that does not understand the namespace, a network transfer that strips them). An ELF section is part of the file itself; nothing short of editing the ELF strips it.

### The `security.peios.sig` xattr

For non-ELF files, the same 65-byte blob lives in an extended attribute:

| Attribute | Value |
|---|---|
| xattr name | `security.peios.sig` |
| xattr value | The 65-byte blob, identical to what an ELF section would hold |

The `security.*` namespace requires privileged access to set — ordinary writes do not propagate to the xattr, which is the security boundary. The image builder sets the xattr at build time using its privileged access; the kernel reads it at exec.

Loss of the xattr (a copy without xattr preservation, a backup-restore through a tool that ignores `security.*`) results in the file being treated as unsigned. The signature blob can be re-applied if the corresponding `.sig` file is preserved, but the xattr layer is not the most robust place for it. ELF binaries get more durability by virtue of their structural signature; non-ELF binaries depend on xattr-preserving operations.

### Detached `.sig` files

During image build, peiso accepts detached signature files alongside the executables they cover. The convention is `<binary>.sig` — a 65-byte file containing exactly the blob that should be stamped as the xattr.

The detached form has no role in a running system. It exists only as a packaging convention so that the build system can keep signatures next to their files without modifying the files themselves. peiso reads the `.sig` files, validates them, stamps the xattrs, and discards the detached forms.

## The content hash

The signature is over a 32-byte SHA-256 hash of the file's content. The bytes that go into the hash differ between ELF and non-ELF files because of how the signature is placed.

### ELF content hash

For ELF binaries, the hash is computed over the binary with the `.peios.sig` **section's contents zeroed**. The section header entry — the entry in the section header table that describes the `.peios.sig` section — is preserved. Only the section's 65 bytes of payload are replaced with zeros for the hash computation.

This rule lets the section travel with the file without the signature signing itself. If the hash were computed over the binary including the signature, the signer would face a chicken-and-egg problem: sign first to know what to put in the section, but the section's contents change the hash. By zeroing the section contents during the hash, the section's *position* and *size* are part of the hash (via the section header) but its *contents* are not.

Verification follows the same rule: the kernel zeros the section contents (in its own working copy, not on disk), computes the hash, and verifies the signature against that hash. If anything else in the binary changed, the hash differs and verification fails.

### Non-ELF content hash

For non-ELF files, the hash is simpler: **SHA-256 of the entire file, byte-for-byte, no exclusions**.

The signature for a non-ELF file does not live in the file, so there is no need to exclude any region from the hash. The xattr holds the signature, the file's bytes are unmodified, and the hash covers all of them.

## Why a section header found means no xattr fallback

A subtle rule worth knowing: if an ELF binary has a `.peios.sig` section header entry (even an empty or malformed one), the kernel uses that path and does **not** fall back to the xattr.

This is to prevent confusion. A binary that *appears* to be ELF-signed but has a corrupt section gives the kernel a deterministic answer: unsigned. The xattr is not consulted as a second chance. The reasoning is to keep the verification rule simple — once the kernel has decided "this is an ELF binary with a signing section", that is the one and only place it looks. A binary that has both a (broken) section and a (working) xattr is also unsigned; the section's existence shadows the xattr.

The implication for someone signing binaries: choose one path per binary. ELF binaries should have a `.peios.sig` section *or* an xattr, not both. Mixed cases are valid but the section wins, and a broken section makes the binary unsigned regardless of what the xattr says.

For non-ELF binaries, the xattr is the only path — there is no section to find. These binaries are signed via xattr exclusively.

## Limits and constants

For completeness:

| Limit / constant | Value |
|---|---|
| Signature blob size | 65 bytes (1 byte version + 64 bytes Ed25519 signature) |
| Version byte | `0x01` in v0.20; anything else is treated as unrecognised |
| Content hash | SHA-256 (32 bytes) |
| Signature algorithm | Ed25519 raw (not Ed25519ph) |
| ELF section name | `.peios.sig` |
| ELF section type | `SHT_PROGBITS` |
| Xattr name | `security.peios.sig` |
| Detached file convention | `<binary>.sig` (build-time only) |
