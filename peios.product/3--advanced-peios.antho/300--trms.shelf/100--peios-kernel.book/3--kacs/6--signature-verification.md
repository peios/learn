---
title: Binary Signature Verification
description: How the kernel verifies signatures on executables and libraries — the key table, finding a signature, hashing, and PIP determination at exec.
---

Binary signing is the foundation of PIP trust determination and of
Library Signature Verification. The kernel verifies cryptographic
signatures on executable files to establish their trust level, and
signing is the *only* mechanism by which a binary acquires PIP
protection — there is no runtime API that can confer it.

This section describes verification. The signature format itself, and
what a signer has to produce, are specified in PSPK's Binary Signing
and PIP chapter. The kernel only ever verifies; it holds no private
key and contains no signing primitive.

## The key table

The kernel carries its verification keys in a dedicated data section
of the kernel image, as an array of 1960-byte entries — a raw
1952-byte ML-DSA-65 public key, then a `u32` little-endian PIP type,
then a `u32` little-endian PIP trust — terminated by an all-zero
entry.

Before any cryptographic work, the whole table is walked and
validated. A table with no all-zero terminator is rejected with
`EINVAL`, and so is a table containing any entry whose tier is not
exactly Protected (512) with `PeiosTcb` trust (8192). Both rejections
fail *every* verification on the system, which is what makes the
single-tier constraint absolute rather than conventional: a key at any
other tier does not merely fail to be honoured, it disables signing
entirely.

The consequence is that a verified binary is always Protected/8192.
The Isolated type (1024) is reserved and unreachable, and the
multi-key, multi-tier model the table layout anticipates would need a
change to the validator, not merely an added key.

A build configured for KUnit compiles in a different, hard-coded key
at the same tier, taken from the test vector header. Such a kernel
trusts a publicly known key.

## Finding a signature

Verification begins by recording the file's current size. Everything
that follows is bounded by that snapshot, and the size is re-read
before the attempt returns — a file that changed size mid-verification
invalidates the whole result.

The first four bytes decide the path. A file matching `\x7fELF` takes
the ELF path; a file shorter than four bytes, or with different magic,
goes straight to the xattr.

On the ELF path the kernel parses the header, locates the section
header table and the section-name string table, and scans sections in
index order for one named exactly `.peios.sig`. The match is over all
eleven bytes including the terminating NUL, so a longer name with that
prefix does not match.

**Finding the section commits the ELF path.** The moment a section
header with that name is found, the xattr is no longer consulted —
whatever happens next. A wrong section type, a size other than 3310, a
range outside the file, an allocation failure, a short read, a bad
version byte, or a hash failure all yield "unsigned" rather than
falling back. This is deliberate: without it, an attacker could craft
a malformed ELF section to force fallback to whichever path they could
more easily control.

Several *structural* ELF failures commit the path too, before any
`.peios.sig` section has been seen: a file shorter than an ELF header,
a class other than `ELFCLASS64`, a byte order other than little-endian,
an unexpected ELF version, a section header entry size other than 64,
an absent or out-of-range section-name string table index, and a
section header table or string table lying outside the recorded size.
A 32-bit or big-endian ELF therefore cannot carry an xattr signature
at all — it is committed to the ELF path and then fails on it. The one
structural case that does *not* commit is `e_shnum == 0`, so an ELF
with no section headers falls through to the xattr normally.

The xattr path reads `security.peios.sig` and requires exactly 3310
bytes; any other size is treated as unsigned. The read bypasses the
LSM xattr hooks, so FACS does not mediate the verifier's own read of
the signature.

## Hashing and verification

The message signed is a 32-byte SHA-256 content hash, computed
differently depending on where the signature was found. For an ELF
section source, the hash covers the file with the section's *contents*
replaced by zeros — the `Elf64_Shdr` entry describing it is hashed
verbatim, along with everything else. For an xattr source the hash
covers the entire file with no exclusions, and that applies to ELF
files reaching the xattr path as well as to non-ELF ones. Hashing
proceeds in 4 KB chunks, with the zero run emitted in
`SHA256_BLOCK_SIZE` pieces.

The kernel then verifies the 3309-byte signature against each key in
the table, in order, returning on the first success. There is no key
identifier in the blob, so key selection is exhaustive trial and the
cost is one ML-DSA verification per key. The trust tier is a property
of *which key verified*, never of anything the signer encoded.

Verification uses the kernel crypto signature API with the `mldsa65`
algorithm. That API exposes no context parameter, so the empty FIPS
204 context is structurally guaranteed rather than checked — a
signature made under a non-empty context simply fails to verify.

A failure to allocate the transform is currently reported the same way
as a signature mismatch. On the exec path that means a kernel lacking
the ML-DSA implementation treats every binary as unsigned rather than
failing loudly, which removes PIP system-wide. On the LSV path the
same condition denies the mapping, which fails closed.

## PIP determination at exec

At `execve()` the kernel looks up and verifies the signature as above.
A verified binary takes `pip_type` and `pip_trust` from the matched
key; no signature, an invalid or unstable one, a bad signature, or no
matching key all yield None/0.

**Exec proceeds in every case.** PIP is additive protection, not an
execution gate: it determines trust level, not permission to run. An
attacker who replaces a signed binary's signature with garbage costs
it PIP protection but can still execute it, subject to FACS. The
asymmetry with LSV — which *does* block unsigned libraries — is
intentional. Exec is permissive; `mmap(PROT_EXEC)` is restrictive.

Determination is transactional with exec success, in three phases. The
pending value is cleared at the top of every `bprm_creds_from_file`
invocation, staged into the task's security blob, and committed to the
process state only from `bprm_committed_creds`. An exec that fails
between staging and commit leaves the process state untouched, and the
stale pending value is cleared by the next exec or at task teardown.

Because the hook fires once per binfmt iteration and each iteration
re-stages, a `#!` script's PIP comes from the **interpreter** — the
last file processed — not from the script. A TCB-signed interpreter
runs at TCB level whatever script it executes. Symlinks need no
special handling either: the LSM hooks receive the already-resolved
target file, so a symlink inherits its target's level by construction.

Once committed, the values are fixed for the lifetime of the process
image, inherited at fork, and re-derived at the child's exec.

## Content pinning

A binary that verifies to a nonzero tier has its backing inode pinned
as KACS-verified executable content before the exec result is
committed, and LSV pins on success too, before allowing the mapping.
Pinning closes the gap between verifying one byte image and modifying
the same inode afterwards.

If pinning fails at exec, the PIP result is **downgraded to None/0**
rather than the exec being failed or the tier being kept — the process
runs unprotected. Under LSV a pin failure denies the mapping instead.

A pinned inode rejects in-place content mutation even when the size
would be preserved: ordinary, positioned and append writes;
`ftruncate()` and pathname `truncate()`; and every `fallocate` mode,
including allocation-only ones, because the pin check runs before and
independently of the mode-support test. File ioctls that mutate
content, ranges, or allocation are rejected, and so are ioctls the
kernel cannot classify — unknown ioctls fail closed on a pinned inode.
Mutation or removal of the `security.peios.sig` xattr is rejected as
well.

The pin is conservative and one-way. It is set once and cleared only
when the inode is allocated or freed, never while the inode is live.
Updating verified executable content therefore means replacing the
inode — write a new file and `rename()` over it — rather than
modifying it in place.

Unsigned, invalid, unstable, bad-signature and no-match attempts never
pin.

## Library Signature Verification

With the `lsv` mitigation enabled, `mmap()` with `PROT_EXEC` on a
file-backed mapping verifies the backing file. An unsigned file, an
invalid or unstable one, a bad signature, or no matching key all deny
the mapping with `EACCES`. On success the library's tier is compared
against the loading process's: the image has to dominate the process,
so a Protected/PeiosTcb process can load only PeiosTcb-or-above
libraries. With one key in the table this reduces to "is it signed
with the TCB key?"

The hash covers the **entire file**, not the mapped region — the whole
file is read and hashed even when only part of it is being mapped, so
the signature covers code in sections this particular mapping does not
touch.

`mprotect()` adding `PROT_EXEC` to a mapping that was not already
executable runs the same checks in a fixed order: WXP, then TLP, then
LSV. Anonymous mappings have neither a path nor a signature, so TLP
and LSV skip them and only WXP applies.

Enabling `lsv` on a running process also re-validates its existing
executable mappings before the bit is committed (§3.3.2), so the
mitigation cannot be turned on over already-mapped unsigned code.

## Revocation

There is none. A signed binary later found to be malicious cannot be
invalidated short of removing it from the filesystem or replacing the
kernel image with a different key. No hash blocklist, no per-key
revocation, and no revocation state of any kind exists.

## Interaction with other mechanisms

**WXP** is orthogonal: it prevents pages being writable and executable
at once, while LSV prevents unsigned executable pages. A process with
both can execute only signed code in read-only pages.

**FACS** runs independently. A signed binary in a directory the caller
cannot reach is still unreachable — the open is denied before signing
is consulted. Signing determines the PIP level of a binary that is
already being executed; it never grants access to one.

**PIP object protection** consumes the result: once a process carries
a tier from its binary's signature, trust labels on objects are
enforced through the AccessCheck pipeline against the `pip_type` and
`pip_trust` held in the PSB (§3.7).
