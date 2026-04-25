---
title: Binary Signing
---

Binary signing is the foundation of PIP trust determination and Library Signature Verification (LSV). The kernel verifies cryptographic signatures on executable files to establish their trust level. Signing is the only mechanism by which a binary acquires PIP protection — there is no runtime API to forge it.

## Key model

The kernel carries one or more Ed25519 public verification keys compiled into the kernel image. Each key is associated with a PIP trust tier:

| Key | PIP type | PIP trust | Description |
|-----|----------|-----------|-------------|
| Peios TCB key | Protected (512) | PeiosTcb (8192) | Core OS components: peinit, authd, loregd, lpsd, eventd. |

Keys are stored as raw 32-byte Ed25519 public keys in a dedicated kernel data section. Each key entry is a struct: `[key: 32 bytes][pip_type: u32le][pip_trust: u32le]` = 40 bytes per key. The key table is terminated by an all-zero entry. v0.20 has exactly one key.

> [!INFORMATIVE]
> Future versions will add additional keys for lower trust tiers (Protected/App, Protected/Authenticode, etc.) managed by authd. v0.20 supports only the TCB key compiled into the kernel. The Isolated PIP type (1024) is reserved; no key is defined for it in v0.20 and pip_type = Isolated will never be set.

Unsigned binaries receive PIP type None (0) and trust 0. There is no intermediate — a binary is either signed with a recognized key or it is untrusted.

## Signature format

Signatures use a common encoding: a version byte (0x01) followed by 64 bytes of raw Ed25519 signature. Total: 65 bytes. v0.20 MUST reject any version other than 0x01.

Two storage locations are supported, checked in priority order:

### Primary: ELF section (for ELF binaries)

ELF binaries store their signature in a `.peios.sig` section. The section type is `SHT_PROGBITS` and contains exactly 65 bytes (version + signature). The ELF section travels with the binary through any file transfer, archive, or distribution mechanism.

**Content hash:** SHA-256 of the ELF file with the `.peios.sig` section contents treated as zero bytes. Specifically: the `sh_size` bytes starting at `sh_offset` (as read from the section header entry) are replaced with zeros in the hash input. The section header table entry itself (the `Elf64_Shdr` struct) is NOT zeroed — it is included in the hash as-is. All other file bytes are included verbatim. This avoids the chicken-and-egg problem while ensuring the section header metadata is integrity-protected.

### Fallback: xattr (for non-ELF files)

Non-ELF files (scripts, data files, non-standard executable formats) store their signature as an extended attribute:

| Attribute | Encoding |
|-----------|----------|
| `security.peios.sig` | 65 bytes: version (0x01) + Ed25519 signature (64 bytes). |

**Content hash:** SHA-256 of the file's entire contents (all bytes from offset 0 to EOF). No exclusions.

### Lookup order

1. If the file is ELF (first 4 bytes = `\x7fELF`): look for `.peios.sig` section. If found and valid, use it. If not found, fall through to step 2.
2. Look for `security.peios.sig` xattr. If found and valid, use it.
3. Neither found: file is unsigned (PIP = None/0).

If both are present, the ELF section takes priority. The rule for ELF files: once a `.peios.sig` section header entry is found in the section header table (by name), the ELF path is committed — any error reading, validating, or verifying the section content (bad version, wrong size, truncated file, verification failure) results in unsigned status. The xattr is NOT checked as fallback. This prevents an attacker from crafting a malformed ELF section to force fallback to a weaker xattr path.

For ELF files that fall through to the xattr path (no `.peios.sig` section header found), the xattr content hash uses the **entire file** (same as non-ELF), not the ELF-section-zeroed hash. The ELF-specific hash is only used when the ELF section is the signature source.

Files shorter than 4 bytes are not ELF — proceed directly to xattr check.

### Signing algorithm

The Ed25519 signature is computed over the content hash (32 bytes) treated as the message: `Ed25519_Sign(private_key, content_hash)`. The kernel verifies as `Ed25519_Verify(public_key, content_hash, signature)`.

> [!INFORMATIVE]
> This is standard Ed25519 signing where the "message" happens to be a 32-byte hash. It is NOT Ed25519ph (which pre-hashes with SHA-512). Any standard Ed25519 library (ring, libsodium, dalek) can sign and verify a 32-byte message directly.

### Distribution

- **ELF binaries** (peinit, authd, loregd, etc.) are self-contained — the `.peios.sig` section survives GitHub releases, tarballs, scp, and any file transfer.
- **Non-ELF executables** (if any) ship with detached `.sig` files. The detached file contains the raw 65-byte blob (version byte + 64-byte signature), identical to the xattr value. The image builder (peiso) reads the detached signature and stamps the `security.peios.sig` xattr during disk image construction. Scripts are NOT signed in v0.20 — PIP for scripts is determined by the interpreter binary's signature (see Scripts and interpreters below).

## Verification at exec (PIP determination)

When a process calls `execve()`, the kernel:

1. Looks up the signature using the lookup order above (ELF section first, then xattr).
2. If no signature found: PIP is set to None/0. Done.
3. Computes the content hash (ELF: file with `.peios.sig` section zeroed; non-ELF: entire file).
4. Verifies the 64-byte signature against each compiled-in public key in table order. The first matching key determines the trust tier.
5. If verification succeeds: sets `pip_type` and `pip_trust` on the new process's PSB from the matched key's trust tier. Done.
6. If verification fails (bad signature, no matching key): PIP is set to None/0. Done.

In all cases, exec proceeds — PIP is additive protection, not an execution gate.

PIP determination is transactional with exec success. If exec fails after PIP has been determined (e.g., mmap failure, OOM), the PSB is not modified — PIP values from the previous binary remain. PIP is only committed to the PSB when exec completes successfully.

PIP values set at exec are fixed for the lifetime of the process image. They are inherited by child processes at fork and reset at the child's exec based on the new binary's signature.

> [!INFORMATIVE]
> A bad or tampered signature does not block execution — PIP is additive protection, not an execution gate. This is intentional: PIP determines *trust level*, not *permission to run*. An attacker who replaces a signed binary's xattr with garbage loses PIP protection but can still execute the binary (subject to FACS access control). The asymmetry with LSV (which does block execution of unsigned libraries) is deliberate: exec is permissive, mmap+PROT_EXEC is restrictive.

## Verification at mmap (LSV)

When a process has the LSV mitigation enabled and calls `mmap()` with `PROT_EXEC`:

1. Looks up the signature using the lookup order (ELF section first, then xattr).
2. If no signature found: reject the mmap (return `-EACCES`).
3. Computes the content hash (ELF: file with `.peios.sig` section zeroed; non-ELF: entire file).
4. Verifies the signature against each compiled-in public key.
5. Determines the library's trust level from the matched key.
6. If verification fails (bad signature, no matching key): reject the mmap (return `-EACCES`).
7. If the library's trust level is below the loading process's PIP trust level: reject the mmap (return `-EACCES`).
8. If the library's trust level is at or above the loading process's PIP trust level: allow.

This means a Protected/PeiosTcb process with LSV can only load libraries signed at the PeiosTcb level or above. A future Protected/App process could load both App-tier and TCB-tier libraries, but not unsigned libraries.

> [!INFORMATIVE]
> For v0.20, with only the TCB key, steps 5-6 reduce to: "is the library signed with the TCB key?" If yes, allow. If no, reject. The trust-level comparison becomes meaningful when multiple keys exist.

## Verification at mprotect

When a process calls `mprotect()` to add `PROT_EXEC` to a mapping that was not originally executable, the following checks apply in order:

1. **WXP** (if enabled): reject if the mapping was ever writable (W→X transition). Applies to all mappings including anonymous.
2. **TLP** (if enabled): reject if the backing file is outside the approved directory prefixes. Applies to file-backed mappings only.
3. **LSV** (if enabled): verify the backing file's signature. Reject if unsigned or insufficiently trusted. Applies to file-backed mappings only.

Anonymous mappings (no backing file) are gated only by WXP. TLP and LSV do not apply to anonymous mappings (they have no path or signature to check).

## Key distribution

The TCB signing keypair is generated at build time by the image builder (peiso). The private key is used to sign TCB binaries during image construction. The public key is compiled into the kernel image. The private key MUST NOT be present on the running system.

## Symlinks

When `execve()` is called on a symlink, the kernel resolves the symlink and opens the target file. The signature xattr is read from the **target file**, not the symlink. A symlink to a signed binary inherits the target's PIP level. A symlink to an unsigned binary is unsigned.

This is correct by construction: the kernel resolves symlinks before the LSM exec hooks fire. No special handling is needed.

## Scripts and interpreters

When `execve()` is called on a script with a `#!` shebang line (e.g., `#!/bin/sh`), the kernel re-execs the interpreter binary. PIP is determined by the **interpreter's** signature, not the script's. A TCB-signed interpreter (e.g., `/bin/sh` signed with the Peios TCB key) runs at PeiosTcb level regardless of what script it executes.

LSV (when enabled on the interpreter process) does not apply to script files — scripts are opened as data (FMODE_READ), not mapped as executable code. LSV only gates `mmap(PROT_EXEC)`.

> [!INFORMATIVE]
> This means a compromised script loaded by a TCB interpreter runs at TCB PIP level. Defense against this is via FACS: the script file's SD controls who can write to it, and the interpreter's SD controls who can execute it. PIP ensures the interpreter process itself cannot be tampered with by non-TCB processes.

> [!INFORMATIVE]
> Future versions MAY add kernel-enforced script signing: the bprm hook for shebang scripts would verify the script file's signature before re-executing the interpreter, requiring scripts to be signed at the interpreter's trust level or above. This is not implemented in v0.20.

## LSV file boundary

For both mmap and mprotect verification, the content hash covers the **entire file**, not just the mapped region. For ELF files, the `.peios.sig` section contents are zeroed in the hash input. For non-ELF files, the hash covers all bytes from offset 0 to EOF. The kernel MUST read and hash the entire file to verify the signature, even if only a portion is being mapped. This ensures the signature covers all code in the file, including sections not mapped by this particular mmap call.

## Revocation

v0.22 provides no per-binary revocation mechanism. A signed binary whose signature is valid against a compiled-in key will be trusted. There is no CRL, no OCSP, no hash-based deny list, and no policy-based revocation.

**Available mitigations for a compromised signed binary:**

- **Filesystem removal.** Delete or replace the binary. Effective on a single machine but requires filesystem access to every affected system.
- **Kernel image replacement.** Rotate the signing key and rebuild the kernel image. All previously-signed binaries are invalidated unless re-signed with the new key. This is a full update cycle.
- **FACS access control.** Remove FILE_EXECUTE from the binary's SD. Prevents execution without removing the file. Does not affect PIP determination for copies the attacker controls.

**What is not available:**

- No mechanism to push a revocation policy across machines before the next OS image update.
- No way to invalidate a specific binary hash while keeping other binaries signed with the same key trusted.
- No timestamping: key rotation invalidates all previously-signed binaries, not just the compromised one.

Future versions may add a kernel-resident hash revocation list (reject specific SHA-256 content hashes even if the signature is valid), populated from the registry at boot and updatable at runtime via a privileged syscall. This would enable targeted revocation without full key rotation.

## Interaction with other mechanisms

- **WXP (Write-XOR-Execute):** Orthogonal. WXP prevents W+X pages. LSV prevents unsigned executable pages. A TCB process with both mitigations can only execute signed code in read-only pages.
- **FACS:** Signing verification runs independently of FACS access control. A signed binary in a directory the caller cannot access is still inaccessible — FACS denies the open. Signing only determines PIP level once the binary is being executed.
- **PIP object protection:** Once a process has PIP set from its binary's signature, PIP trust labels on objects (files, registry keys) are enforced via the AccessCheck pipeline using the process's pip_type/pip_trust from the PSB.
