---
title: Binary signing
type: concept
description: A signed binary carries an Ed25519 signature that the kernel verifies at exec to decide its PIP trust level. Signing is the only path to PIP protection — there is no runtime API to escalate. This page covers what signing accomplishes, how it relates to PIP, and the permissiveness rule that makes signing additive rather than gating.
related:
  - peios/binary-signing/signature-format
  - peios/binary-signing/verification-and-pinning
  - peios/binary-signing/keys-and-image-build
  - peios/process-integrity-protection/overview
---

A **signed binary** carries a cryptographic signature that lets the kernel decide what trust level a process should run at when it execs that binary. The signature is the gate to [process integrity protection](~peios/process-integrity-protection/overview) — every PIP-protected process is PIP-protected because the binary it is running was signed at the appropriate trust level. There is no other way to acquire PIP. No syscall, no privileged operation, no runtime escalation. The signature is it.

The signing model is built on a single principle: **signing only adds trust; it never blocks execution**. An unsigned binary still runs — it just runs as `pip_type = None`, unprotected. A binary with a malformed or invalid signature also runs as None. The signature is the kernel's way of recognising "this binary has been blessed at this level by someone we trust"; its absence or invalidity is "we did not recognise this binary, so we will treat it as untrusted". That is different from "we are not going to let it run". Permissiveness is the rule that distinguishes signing from anti-virus.

## What signing is for

Signing serves one purpose: it lets the kernel assign a PIP type and trust level at exec. The kernel reads the binary, finds (or doesn't find) a signature, verifies it against its compiled-in public-key catalogue, and sets the new process's `pip_type` and `pip_trust` accordingly. From that moment on, PIP enforcement uses those fields.

This is what PIP-protected processes need. peinit, authd, loregd, lpsd, eventd — the TCB daemons — are signed with the TCB key during image build. When the kernel execs them, it sets `pip_type = Protected` and `pip_trust = 8192`. Once running, no non-TCB caller can interfere with them because no non-TCB caller dominates their PIP label.

Without signing, the model has nowhere to anchor. There would be no way for the kernel to know that one binary is the real authd and another is malware impersonating it. The signature is the *attestation* that links a binary on disk to a trust level the kernel will assign at exec.

## Where signing fits in the OS

Signing is a kernel concern, not a userspace one. The kernel:

- Reads the signature blob from the binary.
- Verifies it against the compiled-in public-key catalogue.
- Sets the `pip_type` and `pip_trust` fields on the new process's PSB.

Userspace tools — typically the image builder, `peiso` — produce the signature at build time. They have the private key, compute the hash, generate the signature blob, attach it to the binary, and ship it. After that, the private key MUST NOT be present on any running Peios system. Verification is public-key only; the only credential a running system needs is the public key, which is compiled into the kernel image.

The split between userspace signing and kernel verification means a Peios system can never sign new binaries itself. Distribution of new signed binaries happens through the package system, with signatures produced offline by whoever holds the relevant private key.

## The permissiveness rule

The kernel's behaviour when a signature is absent or invalid is the design decision that distinguishes signing from anti-virus.

| Condition at exec | Result |
|---|---|
| No signature at all | Process runs at `pip_type = None`, `pip_trust = 0`. |
| Signature present, version byte unrecognised | Same. |
| Signature present, key not in catalogue | Same. |
| Signature present, but bytes do not verify (hash mismatch) | Same. |
| Signature present and verifies against a catalogue key | Process runs at the PIP level the catalogue entry specifies. |

The first four rows all produce the same outcome: the exec succeeds, the process runs at None. The fifth row produces a PIP-protected process. In no case does the exec fail because of signing.

The rationale: signing is the layer that **adds** trust to specific binaries. It is not the layer that decides "only these binaries may run". A user-mode application not signed at any level should still run; it should just not have PIP protection. The mechanism that decides what may run at all is mount policy (FACS), file permissions (DACL), and capabilities (KACS). Signing is a separate axis that sits on top.

This is why signing does not have a "policy" you configure to "require all binaries to be signed". The kernel does not enforce that. The signing layer itself is permissive.

The corollary is that **`mmap(PROT_EXEC)`** is *not* permissive — that is one of the [Process mitigations](~peios/process-mitigations/overview) (LSV, Library Signature Verification), and it enforces signing for libraries loaded into a PIP-protected process. But that is the mitigation, not the signing layer. Signing decides PIP at exec; LSV decides what libraries may then be loaded.

## What signing does not do

A few clarifications:

- **Signing does not authenticate the user.** A binary signed at TCB level run by an ordinary user is still a TCB-level process from PIP's perspective. The user is not the signer; the signer is whoever owned the private key when the binary was built. Identity-vs-trust is the two-axis story.
- **Signing does not prevent execution.** A binary that fails verification still runs. The signing layer does not gate exec; it gates PIP.
- **Signing is not revocation.** A previously-trusted binary later found to be malicious cannot be invalidated short of removing it from the filesystem or replacing the kernel's public-key catalogue. There is no hash-based revocation list in v0.20.
- **Signing does not verify provenance.** The signature confirms that whoever held the corresponding private key produced this exact bytes-on-disk. It does not confirm where the binary came from, who built it, or whether it does what its name suggests.
- **Signing does not handle scripts.** A script is not a signed binary; the script's PIP comes from the interpreter's PIP. See [Verification and pinning](~peios/binary-signing/verification-and-pinning).

## What the user sees

For most users, signing is invisible. A binary built into the Peios image — `peinit`, `authd`, the rest — is signed by `peiso` during build, and the user never sees the process. When they exec these binaries (or peinit execs them on the user's behalf), the kernel verifies the signature and sets PIP, and the binary runs as expected.

For binaries distributed through the package system, the package's `.peipkg` is itself signed at the package layer (different from the binary-signing layer this topic covers), and the binary inside it may or may not carry a Peios-format signature for PIP purposes. In v0.20, only TCB binaries do. Future versions may add Authenticode-style App and third-party tiers.

For binaries the user produces — a compiled program, a self-built tool — there is no signature, exec runs them at `pip_type = None`, and they get no PIP protection. They are still bound by all the other access control layers; they just are not high-trust.

## Where to start

If you want the on-disk format — what the signature blob actually looks like, where it lives in an ELF binary, how non-ELF files carry it — read [Signature format](~peios/binary-signing/signature-format).

If you want the kernel's behaviour at exec — how verification proceeds, the stable-snapshot rule, what content pinning does after a binary is verified, and how scripts and interpreters interact — read [Verification and pinning](~peios/binary-signing/verification-and-pinning).

If you want the key management story — where the TCB key lives, how `peiso` uses the private key at build time, the constraints on key handling — read [Keys and image build](~peios/binary-signing/keys-and-image-build).
