---
title: Process Trust
type: concept
description: Separate account authority, executable trust, and process hardening when operating services.
---

A process has an identity token, a security descriptor, and a Process
Security Block (PSB). They answer different questions:

- The token identifies the caller and its authority.
- The target process descriptor controls which operations that caller can
  request.
- PIP fields in the PSB describe executable trust. Mitigation fields describe
  committed process protections.

Impersonation changes the effective token, not the process's PIP tier.
An administrator identity does not turn an unsigned debugger into a trusted
process, and a trusted service does not acquire every client's authority
merely by receiving a request.

## Interpreting a refused process operation

For protected process boundaries, the caller needs the required descriptor
right and sufficient PIP dominance. Dominance compares both type and trust;
it does not replace the operation-specific descriptor check.
`SeDebugPrivilege` can rescue the descriptor check, but cannot rescue failed
dominance. Kernel-mediated service control through Peinit is distinct from
directly signaling the service from a shell.

Inspect the target's PSB separately from its token and descriptor. PSB queries
have a documented limited-query exception to dominance; that does not imply
permission to trace, signal, or open the target's token. A visible PID also
does not imply access to its metadata. The
[kernel reference](~kernel/internals/kacs/executable-trust/process-integrity-protection)
owns operation mappings, self-operation exceptions, partial multi-target
signal success, and the limits of PIP.

PIP is enforced by a trusted kernel. It does not defend against a compromised
kernel, unrestricted DMA, or a hostile hypervisor. Protected-process core
dumps are disabled in the maintained implementation; do not assume a
high-trust crash collector is installed.

## Signing and running a binary

A valid executable signature establishes a tier only if the running kernel
trusts its public key. The maintained validator accepts Protected/PeiosTcb
entries; adding entries for hypothetical tiers requires an implementation
change. A listed key does not prove the complete table passes validation.

Ordinary unsigned binaries can run without a PIP tier. That is different from
failure of the verification machinery, which can refuse execution, and from
kernel-initiated helpers, which require TCB trust. Executing under a tracer
or supervisor can cap a would-be trust increase. Read back the running
process's state instead of inferring its tier from a package or filename.

For a script, the final interpreter determines the execution tier. A symlink
resolves to the target file. Verified content can be pinned against in-place
mutation; pinning is not released merely because the process exits. A failed
exec can leave content pinned. Use the deployment's replacement-file workflow
for updates rather than assuming signed files remain editable in place.

The [verification reference](~kernel/internals/kacs/executable-trust/signature-verification)
and [exec lifecycle](~kernel/internals/kacs/executable-trust/exec-and-library-integrity)
define these rules. The
[signature specification](~specifications/pspk/binary-signing-and-pip/signature-format)
owns the wire format and hashing rules. Detached package signatures are a
transport convention, not another kernel runtime lookup path.

## Build and release trust

Keep private signing keys in controlled signing infrastructure. Runtime
verification needs public keys and signatures, not private keys. Record the
kernel's trusted public-key fingerprints and the signing provenance of the
artifacts deployed with it. A development or KUnit key is not release trust.

Package authenticity, executable PIP signatures, module signatures, and
firmware verification serve different purposes. Successfully producing a
Bazel package does not establish that every required signing step or image
composition step occurred. The retired Pekit image recipe is not a supported
replacement for the deferred PPK image composer.

The kernel has no runtime signing-key replacement or per-binary revocation
service. Key compromise requires a coordinated kernel/key and artifact
replacement plan; removing a file alone does not revoke copies elsewhere.
Do not promise additional signing tiers or a third-party signing service
until their verification and operational support exists.
