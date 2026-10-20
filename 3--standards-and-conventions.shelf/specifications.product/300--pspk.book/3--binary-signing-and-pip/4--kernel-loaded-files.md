---
title: Files the Kernel Loads
description: The same signature, required on device firmware the kernel reads for its own use — what a firmware signer must produce and what the verifier does with it.
---

Executing a binary is not the only way file contents become code.
When a driver asks the kernel for device firmware, the kernel reads a
file from the filesystem and hands its bytes to hardware that can act
on host memory. A tampered firmware blob is at least as complete a
compromise as an unsigned binary running at the highest tier, and it
happens without an exec for the verifier to intercept. This section
extends the signature of §3.2 to those files.

## What is covered

The verifier checks a signature on every file it reads through the
firmware loader — the mechanism a driver uses to request a named
blob, whether whole or in pieces. Files the kernel reads for other
purposes (a module, a policy file, a kexec image) have their own
integrity mechanisms and are not covered here.

Firmware is not executed by a process, so it obtains no PIP identity.
The signature is used for one decision only: whether the bytes reach
the device.

## What a signer produces

A firmware file is never ELF. The signer therefore produces the
extended-attribute form of §3.2 — the 3310-byte blob over SHA-256 of
the **entire file as it sits on disk** — and delivers it as the
detached-signature payload entry of PSPU §5.16, `<file>.peios.sig`
beside the file in the package. The package consumer derives
`security.peios.sig` from it when the file is created.

Because the hash covers the on-disk bytes, a compressed blob is signed
in its compressed form. The kernel verifies before it decompresses,
which is the side of that boundary a verifier has to be on: the
decompressor is code that runs on untrusted input, and it must not run
on bytes that have not yet been checked.

A signer MUST NOT sign a symlink. The verifier reads through links
and checks the target's attribute; a signature on the link itself is
never consulted.

## What the verifier requires

The verifier resolves the signature by the lookup of §3.2 and selects
a key by the trial of §3.2. It then requires that the key's tier be
the one that denotes the kernel's own trusted computing base
(PeiosTcb). A verified signature from a key at any other tier is
treated exactly as no signature: firmware runs with kernel privilege
on the far side of a bus, and no lower tier is fit to supply it.

A firmware file that is unsigned, unverifiable, or signed at an
insufficient tier is **refused**: the loader reports failure to the
requesting driver, which fails as it would for a missing file. The
verifier MUST NOT fall back to loading the file unsigned.

A verifier MAY provide a boot-time policy that reports rather than
refuses such a file, so that a system can be brought up with an
unsigned firmware set and the gaps found before refusal is turned on.
A verifier in that mode MUST record every file it would have refused,
and MUST NOT make the mode selectable at run time.

## What a signer may rely on

- The bytes verified are the bytes delivered to the device. The
  verifier checks the buffer the loader will hand over, not a separate
  read of the file, so a file changed between the two is not a concern
  the signer has to design around.
- The check applies to every path the loader resolves, including
  paths an administrator has added to its search list. A signer
  cannot be shadowed by an unsigned file earlier in that list.
- The check does not apply to firmware pushed into a device by means
  other than the loader — a device's own update interface, for
  example. Those are the responsibility of the driver that exposes
  them.
