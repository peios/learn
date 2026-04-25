---
title: PSB Fields
---

## Protection (set at exec, fixed)

| Field | Type | Description |
|---|---|---|
| `pip_type` | enum | Process Integrity Protection type: Isolated, Protected, or None. Determined by the binary's cryptographic signature at exec time. |
| `pip_trust` | uint | Trust tier within a PIP type. Higher values can access lower. Determined by the binary's signer identity. |

PIP fields are signing-based. At exec, the kernel MUST verify the binary's cryptographic signature and determine `pip_type` and `pip_trust` from the signer's identity. The verification algorithm and key model are specified in the Binary Signing section. The parent process MUST NOT be able to influence PIP determination — even a compromised peinit running as SYSTEM MUST NOT be able to forge PIP protection for an unsigned binary.

When `pip_type` is set to a value other than None at exec, the kernel MUST also set `lsv` (Library Signature Verification) on the PSB automatically. PIP without LSV is never correct — a Protected process that loads unsigned libraries has a code injection path that defeats the purpose of PIP. This is the only mitigation that is coupled to PIP; all other mitigations remain independently controlled by peinit.

The public verification key is compiled into the kernel image. The kernel only verifies signatures; it MUST NOT sign.

> [!INFORMATIVE]
> This differs from the reference model, where the parent process can set a protection level attribute at process creation while the kernel validates the binary's signature. Peios removes the parent-controlled aspect entirely — the kernel determines PIP from the signature alone.


## Process mitigations (one-way)

| Field | Type | Description |
|---|---|---|
| `lsv` | bool | **Library Signature Verification.** Only signed shared libraries MAY be loaded. When the process has `pip_type != None`, the library's trust level must be at or above the process's PIP trust level. When the process has `pip_type = None`, any valid signature suffices (trust level is not compared). See the Binary Signing section. |
| `wxp` | bool | **Write-XOR-Execute Protection.** Memory pages MUST NOT be simultaneously writable and executable. W+X mappings and transitions between writable and executable MUST be rejected. |
| `tlp` | bool | **Trusted Library Paths.** Shared libraries MAY only be loaded from approved directory prefixes. Weaker than LSV (trusts the path, not the binary). The approved prefixes are a machine-wide kernel cache, populated at boot by peinit from the registry. See the TLP cache below. |
| `cfif` | bool | **Forward-Edge Control Flow Integrity.** Hardware indirect-branch tracking (Intel IBT, ARM BTI) is locked on and MUST NOT be disabled by the process. |
| `cfib` | bool | **Backward-Edge Control Flow Integrity.** Hardware shadow stack (Intel CET shadow stack) is locked on and MUST NOT be disabled by the process. |
| `pie` | bool | **Position-Independent Executable Requirement.** Non-PIE binaries MUST be rejected at exec time. Ensures ASLR is effective. |
| `sml` | bool | **Speculation Mitigation Lock.** Speculation mitigations are locked on and MUST NOT be disabled by the process. |

Mitigations are inherited from the parent at fork and MAY be set via syscall (typically by peinit between fork and exec). They are one-way: once set, they MUST NOT be cleared. Exec MUST NOT reset mitigations — a mitigation set by the process launcher persists regardless of what binary is loaded.

This is distinct from PIP, which is determined at exec from the binary's signature. Mitigations are set by the process launcher as policy; PIP is determined by the kernel as a property of the binary.

> [!INFORMATIVE]
> These mitigations compose: LSV ensures only signed libraries load, WXP blocks code injection, CFIF blocks forward-edge code reuse (indirect calls/jumps), CFIB blocks backward-edge code reuse (return-oriented programming), and PIE ensures ASLR is effective. Together they make exploitation dramatically harder.

## UI access (one-way)

| Field | Type | Description |
|---|---|---|
| `ui_access` | bool | Permits interaction with higher-integrity UI elements. Reserved for future desktop functionality. Set via syscall (typically by peinit between fork and exec), fixed thereafter. |

## Process restrictions (one-way)

| Field | Type | Description |
|---|---|---|
| `no_child_process` | bool | Once set, the process MUST NOT create child processes (fork/clone without CLONE_THREAD). New threads are unaffected. MUST NOT be cleared once set. |

Unlike the exec-time fields, `no_child_process` MAY be set at two points:

1. **Between fork and exec.** The parent's code, running in the freshly forked child, calls a KACS syscall to set the flag on itself before exec. The new binary loads with the restriction already in place.
2. **At runtime by the process itself.** A process MAY restrict itself at any time (e.g., after spawning worker processes).

## TLP cache (machine-wide)

The approved directory prefixes for TLP enforcement are stored in a global kernel cache, not on individual PSBs. The PSB `tlp` flag controls whether a process is subject to TLP enforcement; the paths themselves are shared.

Cache structure: an array of UTF-8 directory prefix strings. Maximum 64 entries, maximum 4096 bytes per path. The mechanism for populating and updating the cache is defined by the registry subsystem (loregd) and is outside the scope of this section.

At mmap(PROT_EXEC) time, when the process has TLP enabled, the kernel checks whether the mapped file's path starts with any approved prefix. If no prefix matches, the mmap is rejected. If the cache is empty, all PROT_EXEC mappings are denied for TLP-enabled processes.

## Identity virtualization (reserved)

| Field | Type | Description |
|---|---|---|
| `virtualization` | reserved | Per-process state for setuid compatibility redirection. Not active in v0.20. Implementations MAY omit this field until activated. |

## Process security descriptor

Every process carries a security descriptor that controls who can perform operations on it. The process SD is stored on the PSB alongside the PIP and mitigation fields.
