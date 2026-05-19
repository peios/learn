---
title: Keys and image build
type: concept
description: The kernel's public-key catalogue is compiled into the kernel image at build time. The corresponding private keys are held by image builders and MUST NOT be present on a running Peios system. This page covers the key catalogue, the peiso image-build flow, the constraints on key handling, and the v0.20 limitation of one signing key.
related:
  - peios/binary-signing/overview
  - peios/binary-signing/signature-format
  - peios/binary-signing/verification-and-pinning
  - peios/process-integrity-protection/overview
---

A signed binary's trust level is whatever the **key that signed it** says it should be. The mapping from "this key" to "this PIP level" is the kernel's public-key catalogue. The catalogue is compiled into the kernel image; there is no way to add keys to a running system, and there is no way to remove them either short of replacing the kernel.

This page covers the catalogue's structure, who holds the private keys, how `peiso` (the image builder) uses them, the constraints on key handling, and the v0.20 limitation of having only one key.

## The catalogue

The kernel holds an in-memory table mapping each known public key to the PIP level its signature confers. Each entry is structured:

| Field | Size | Meaning |
|---|---|---|
| Public key | 32 bytes | The raw Ed25519 public key. |
| `pip_type` | 4 bytes (little-endian u32) | The PIP type this key represents. |
| `pip_trust` | 4 bytes (little-endian u32) | The PIP trust level this key represents. |

Each entry is 40 bytes. The table is a contiguous array of entries terminated by an all-zero entry — the kernel walks until it sees a sentinel.

At exec, when the kernel verifies a signature, it tries each key in the table in turn until one verifies the signature or the table runs out. If a key verifies, its `pip_type` and `pip_trust` are written to the new process's PSB. If no key verifies, the binary is treated as unsigned.

The table is part of the kernel image. It is read-only at runtime; there is no syscall to add an entry, modify an entry, or remove one. Replacing the table requires replacing the kernel.

## What v0.20 actually contains

In v0.20, the catalogue has **one entry**: the **TCB key**. The mapping is:

| Key | `pip_type` | `pip_trust` | What it represents |
|---|---|---|---|
| TCB public key | 512 (Protected) | 8192 | Peios TCB binaries — peinit, authd, loregd, lpsd, eventd |

That is it. No App-level key, no Authenticode key, no AntiMalware key. The categorical PIP labels described in [Process integrity protection](~peios/process-integrity-protection/overview) — Protected/1024 for Authenticode, Protected/1536 for AntiMalware, Protected/2048 for App, Protected/4096 for Peios — are *defined* in the model but no key in v0.20 corresponds to them. No binary on a v0.20 system will have these PIP values because nothing exists to sign them at those levels.

The implication: every signed binary on a v0.20 Peios system runs at PIP Protected/8192. There are no other PIP-protected processes. PIP is binary: a process is either TCB-level or unprotected.

Future Peios versions will add keys for the other tiers. App-level signing will let Peios-distributed applications get their own PIP protection (mid-trust); Authenticode-level will let third-party signed binaries run at low-but-non-zero trust; AntiMalware-level will protect security tooling. The catalogue grows; the model accommodates it without code changes.

## The TCB private key

The TCB **private key** is what `peiso` uses to sign TCB binaries at image build. It is the most security-sensitive artefact in the entire system: anyone with the TCB private key can sign a binary that the kernel will then trust at the highest level. There is no revocation, no per-binary blocklist, no way to invalidate a signed binary short of removing it.

The constraints on the private key are absolute:

- **The TCB private key MUST NOT be present on any running Peios system.** It is for image build, and only image build. A running system has no need for the private key — the kernel verifies with the public key only.
- **The key is held by whoever builds the system image** (in practice, the Peios project's release infrastructure for the official distribution; potentially a downstream packager for a fork).
- **The key is not distributed.** Users do not get a copy of the private key. They get the binaries the private key was used to sign.

The standard pattern: build infrastructure with the private key produces image artefacts. The artefacts include the public key compiled into the kernel image and the signed TCB binaries. The artefacts ship; the private key stays in the build infrastructure.

A system whose private key has been compromised loses the security guarantees of PIP. There is no way to retroactively recover from such a compromise; the only fix is to release a new image with a new public key and re-sign all TCB binaries with the new private key, then deploy. Existing systems running the old image continue to trust the old key.

## peiso and the build flow

`peiso` is the Peios image builder. Its job is to assemble a complete bootable Peios image — kernel, root filesystem, signed binaries, build artefacts. Signing is one of its tasks.

At build time, peiso:

1. Compiles or assembles the kernel image. The public-key catalogue is built into this image; peiso embeds the kernel-build's public keys (or asserts that they are already embedded).
2. Collects the binaries that should be signed at TCB level. The full list is defined per release — typically peinit, authd, loregd, lpsd, eventd.
3. For each binary, peiso:
   - Computes the appropriate content hash (ELF section zeroed for ELF, full file for non-ELF — see [Signature format](~peios/binary-signing/signature-format)).
   - Signs the hash with the TCB private key, producing a 64-byte Ed25519 signature.
   - Constructs the 65-byte blob (version byte + signature).
   - For ELF binaries: inserts the `.peios.sig` section with the blob as its content, then re-computes the hash (now over the binary including the populated section, with the section zeroed during hashing per the ELF rule) and re-signs. (In practice the section is reserved with zeros first, then the signature is computed against the same zeroed bytes, then the section is populated; the resulting hash matches whatever the kernel will compute at verification time.)
   - For non-ELF binaries: writes the blob as a detached `.sig` file next to the binary. At image-assembly time, peiso reads the detached file and stamps the `security.peios.sig` xattr on the binary in the image's filesystem.
4. The signed binaries are placed in the image. The detached `.sig` files are discarded.
5. The image is finalised and emitted as an installable artefact.

At runtime — when the image boots — the kernel reads its own embedded public key, the TCB binaries' embedded sections (or xattrs) provide their signatures, and verification proceeds. No private key is involved at runtime.

## Why one key in v0.20

A reasonable question: why does v0.20 ship with only the TCB key? Why not at least an App key for Peios-distributed applications?

The answer is that the App, Authenticode, and AntiMalware tiers require infrastructure that v0.20 does not have:

- **App-level signing** requires a Peios-managed signing service that signs released applications. The service exists conceptually; the operational pipeline does not.
- **Authenticode-level signing** requires a trust agreement with one or more third-party CAs or a Peios-managed equivalent. None of that is in place.
- **AntiMalware** requires a vetting process for security-tooling vendors. Same status.

The TCB key, by contrast, is just the project's own key, used to sign the project's own binaries. The infrastructure is the project's own release pipeline. It works on day one.

Future Peios versions will add the other tiers as the corresponding infrastructure comes online. The model accommodates them. The catalogue grows. Until then, the only PIP-protected processes are TCB processes, and the model effectively has two levels: TCB and not-TCB.

## Implications for ordinary deployments

For someone running Peios:

- **No signing tools are available on a running system.** You cannot sign your own binaries to get PIP protection. The TCB private key is not available; no other key is defined.
- **Binaries you write or compile yourself run as `pip_type = None`.** Including binaries built from source on the running Peios system. This is correct behaviour — there is no path for an untrusted-by-the-OS binary to acquire trust.
- **The only PIP-protected processes are TCB.** peinit, authd, loregd, lpsd, eventd, and that is it. Everything else runs at None.
- **Updates to TCB binaries come through the package system.** A new release of authd, say, is in a `.peipkg` signed by the project's package-signing infrastructure (separate from the TCB binary signing — packages have their own signature for distribution integrity). The binary inside the package carries the TCB-key signature for PIP. Installing the package places the binary on disk; the kernel verifies it at next exec.

For administrators of a custom Peios fork (using their own kernel image with their own key catalogue), the same model applies with whatever keys they have defined: their TCB-equivalent key signs their TCB binaries, those binaries run at TCB-equivalent PIP, and nothing else has PIP protection unless they add keys to their catalogue.
