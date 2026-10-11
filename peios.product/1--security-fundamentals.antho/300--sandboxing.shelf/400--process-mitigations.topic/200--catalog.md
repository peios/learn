---
title: Catalog
type: reference
description: The mitigation flags, their threat models and compatibility limits, and the difference between a named protection and one that can be activated.
related:
  - peios/process-mitigations/overview
  - peios/process-mitigations/applying-and-lifecycle
  - peios/binary-signing/overview
---

This catalog covers eight named protections plus the reserved UI_ACCESS slot. A defined flag is not a guarantee that it can be activated on a given process or platform. The [Kernel TRM](~peios/advanced-peios/peios-kernel/kacs/process-security-block/fields#process-mitigations-one-way) documents activation-backed, all-or-nothing requests and current implementation limits; [Applying and lifecycle](~peios/process-mitigations/applying-and-lifecycle) explains how to inspect the committed state.

The entries retain the threat model of each protection. Read the support and lifecycle limits alongside it before choosing a service policy. The numeric `KACS_MIT_*` values are cataloged in [Other constants](~peios/advanced-peios/constants-and-catalogs/other-constants) and the [Kernel ABI](~peios/advanced-peios/peios-kernel/kacs/kacs-abi#process-mitigation-bits).

## LSV — Library Signature Verification

LSV decides which file-backed executable code may be loaded into the process. It requires a valid signature. For a PIP-protected process, the library must also meet the process's PIP trust floor; for a process with no PIP protection, a valid signature is still required but the trust floor is not compared.

The kernel's behaviour:

- When `mmap(..., PROT_EXEC, ...)` is called on a file fd, the kernel checks the file's signature.
- If the file has no signature, or its signature is invalid, the call fails with `-EACCES`.
- If the caller is PIP-protected and the file's valid signature is below its required trust, the call also fails with `-EACCES`.
- If the file's signature is valid and meets the applicable trust requirement, it passes the LSV check. Other mitigation or access checks may still refuse the operation.

A TCB process (`pip_trust = 8192`) can therefore load only libraries meeting that trust. The conceptual tier model also describes an App tier (`2048`) that would need App-or-higher libraries rather than Authenticode or unsigned ones; the [Kernel TRM](~peios/advanced-peios/peios-kernel/kacs/process-security-block/fields#protection-set-at-exec-fixed) currently documents only Protected/PeiosTcb as producible. Do not use a hypothetical tier as evidence of deployed support. A process with no PIP protection is still subject to LSV signature checks when the flag is on.

Activation also validates existing file-backed executable mappings. A process cannot first load unsigned code and then successfully commit LSV over it. Adding executable permission with `mprotect` runs the same verification; anonymous executable mappings are governed by WXP rather than LSV. See [Library Signature Verification](~peios/advanced-peios/peios-kernel/kacs/signature-verification#library-signature-verification).

LSV is the mitigation that closes the "load arbitrary shared object" injection path. An attacker who has overwritten a function pointer in the process to point at `dlopen("evil.so")` finds that the call fails — the kernel refuses to map the unsigned library as executable.

LSV is relevant to PIP-protected services such as peinit and authd, but the service name or signing tier is not proof that it is enabled. Check the required policy, library compatibility and committed state.

## WXP — Write-XOR-Execute

WXP rejects writable-and-executable mappings and transitions between writable and executable protection. These are the invariants documented by the Kernel TRM.

Specifically:

- `mmap(..., PROT_WRITE | PROT_EXEC, ...)` is refused if WXP is enabled.
- An `mprotect` transition from writable to executable is refused.
- An `mprotect` transition from executable to writable is refused.

The [Kernel TRM](~peios/advanced-peios/peios-kernel/kacs/process-security-block/fields#process-mitigations-one-way) establishes transition checks and validation of observable existing state. It does not establish a lifetime history of every page's earlier protections; do not rely on that stronger model when assessing compatibility.

The effect: JITs (Just-In-Time compilers) cannot run with WXP enabled. A JIT's whole job is to allocate a region of writable memory, generate code into it, then flip the region executable — exactly what WXP refuses. Binaries that need this flexibility (managed-language runtimes, dynamic-recompilation engines) cannot be hardened with WXP.

A native binary that loads its executable code from disk and uses writable, non-executable stack and heap may not need these transitions. That is a compatibility consideration, not proof that every native binary is unaffected: review the program's actual mapping requirements.

WXP activation also checks existing mappings: the Kernel TRM specifies failure for an existing writable-executable mapping or another observable invariant violation. A late request is not an exemption for code generation done earlier.

WXP is one of the cornerstones of process hardening. It closes the "inject shellcode and jump to it" pathway: an attacker who has corrupted memory cannot make their corrupted region executable. The exploit's payload, no matter how big, is just data.

## TLP — Trusted Library Paths

TLP gates the paths used for file-backed executable mappings. The kernel compares the resolved absolute backing path against a machine-wide cache of approved directory prefixes for `mmap(PROT_EXEC)` and when `mprotect` adds execute permission.

**Current implementation limit:** the [Kernel TRM](~peios/advanced-peios/peios-kernel/kacs/process-security-block/fields#the-tlp-cache) states that the cache has no production writer: no syscall, securityfs node or registry path fills it. Only a KUnit test helper populates it. The documented shipping cache is therefore empty, so it matches no path. Do not assume that peinit fills a usable library allowlist at boot or that editing the registry can do so.

The check:

- The kernel resolves the file's path to an absolute pathname.
- The absolute path is compared against each entry in the TLP cache.
- If the path begins with an entry's prefix, it passes the TLP check. Other checks still apply.
- If not, the operation fails with `-EACCES`.

Paths such as `/usr/lib/`, `/lib/` or a service-specific directory illustrate possible prefixes, not installed cache entries. `/tmp/`, `/home/` and every other path fail when none of the configured prefixes matches; with the documented empty production cache, even system-library paths fail.

The threat model is loading executable code from an untrusted location, such as an attacker writing a shared object into `/tmp/` and loading it with `dlopen`. A useful path policy would allow only suitably protected directories; a trusted-looking pathname alone does not prove the directory cannot be modified. TLP checks the prefix, while filesystem access control determines who can write there.

TLP and LSV have complementary models: LSV requires an acceptable signature; TLP requires an approved location. That does not make their combined activation a safe default. TLP also validates existing file-backed executable mappings and fails if their paths cannot be resolved or accepted, including when the cache is empty. Anonymous mappings are outside TLP and LSV; WXP governs them.

TLP cache details:

- Maximum 64 entries.
- Each entry is an absolute directory-prefix byte string, beginning and ending with `/`, checked against kernel-resolved path bytes. The trailing slash prevents `/usr/lib/` from matching `/usr/libevil`.
- Maximum 4096 bytes per path.
- The cache is machine-wide. Empty, relative, NUL-containing or non-slash-terminated prefixes are invalid; the Kernel TRM specifies atomic rejection of invalid updates. No supported production population route is documented.

## CFIF and CFIB — Control Flow Integrity (Forward and Backward)

CFIF (Forward) and CFIB (Backward) name separate control-flow protections: indirect-call/jump target checking and return-address checking. Do not assume both are available because both have flag values. The Kernel TRM currently documents CFIF as unavailable and CFIB activation as self-only.

The legacy request flag `CFI` (0x008) expands to CFIF (0x040) and CFIB (0x080); the alias is not stored in readback. Requesting the alias still requests the unavailable CFIF half, so it is not a shortcut around activation limits. Application code should name the specific supported protections its policy requires.

### CFIF — Forward CFI

The forward-CFI model rejects indirect calls and jumps (function pointers, vtables) that land at an instruction other than a designated call target. On x86_64, the hardware mechanism is IBT (Indirect Branch Tracking) — every legitimate target of an indirect branch is marked with an `ENDBR64` instruction; an indirect branch landing somewhere without `ENDBR64` traps.

Such enforcement would require placing the process in IBT-enforcing mode, where an indirect branch to a non-`ENDBR64` target raises a control-protection fault. **The Kernel TRM says CFIF cannot currently be committed:** activation against a live task returns `ENODEV` because no userspace IBT/BTI control surface is exposed. Treat a request as failed, not as silently active protection.

The threat model is code reuse through unintended indirect-call and jump targets, including JOP gadgets in legitimate code. Return-oriented programming uses return-address manipulation, covered by the separate backward-CFI model below. The presence of ENDBR instructions in a binary is not evidence that CFIF enforcement was activated.

### CFIB — Backward CFI

CFIB refuses `ret` instructions that do not return to the address pushed by the corresponding `call`. The hardware mechanism is the shadow stack — a separate stack maintained by the CPU that records return addresses. Every `call` pushes onto both the data stack and the shadow stack; every `ret` pops both and compares them. A mismatch traps.

With CFIB enabled, the kernel ensures the process runs with the shadow stack engaged. An attacker who overwrites a return address on the data stack cannot get the `ret` to honour their overwrite — the shadow stack still has the original address; the comparison fails; the process dies.

The threat closed: classic ROP. Overwriting return addresses is the foundation of return-oriented exploitation; CFIB makes the trick impossible (or, more precisely, makes it lead to immediate process termination instead of attacker-chosen execution).

Hardware mechanisms such as Intel CET and architecture-specific BTI/PAC facilities illustrate why control-flow protection needs platform and program compatibility; they are not a cross-platform support guarantee. The Kernel TRM describes CFIB through shadow-stack enable-and-lock and rejects activation on a task other than the caller. A program must use a supported self-hardening route and check the result.

Unsupported architecture-backed activation fails closed. It is not a successful no-op on an incompatible platform or program. Do not infer protection from compiler flags alone; verify the committed mitigation state.

## PIE — Position-Independent Executable

PIE refuses exec of binaries that are not position-independent. The kernel checks the ELF image type at exec; if PIE is enabled on the process's PSB and the new binary is not PIE-built, the exec fails with `-EACCES`.

PIE-built binaries are loaded at randomised addresses every time they exec — Address Space Layout Randomisation (ASLR) covers the executable's own segments, not just the heap and shared libraries. An attacker who would have needed to know the address of a specific instruction in the binary to construct a ROP chain finds the address randomised and unpredictable.

A non-PIE binary has fixed addresses for its code and globals. Every exec puts them in the same place. An attacker can compute exploitation gadget addresses once and reuse them across runs.

PIE must be committed before the exec it is intended to constrain; setting it afterward does not prove that the current binary was checked at launch.

For build compatibility, PIE builds use compiler/linker options such as `-fPIE -pie`. Even when a distribution builds PIE binaries by default, verify the service's actual packaged binary; a local or emergency rebuild can lose the property.

Position-independent code can change addressing and indirection, including GOT/PLT use, with a performance cost that depends on the toolchain, architecture and workload. Do not use a fixed percentage as a compatibility or capacity guarantee.

## SML — Speculation Mitigation Lock

SML locks speculation mitigations on for the process. The threat family includes speculative-execution side channels such as Spectre, Meltdown and MDS; available defences and their cost depend on the platform. The Kernel TRM describes activation through the architecture's kernel interface, with failure if protection cannot be made effective. It also accepts a platform reporting speculation as unconditionally not affected, with nothing to enable. A committed SML flag is not a list of particular barriers, buffer clears or microcode operations applied on every context switch.

The performance cost can be significant and depends on the CPU and workload. Review the security requirement and capacity impact for secrets-handling processes such as cryptographic key holders, sealed-secret stores and TCB services; neither a fixed overhead estimate nor a blanket claim that a workload does not need SML establishes the right policy.

SML is a per-process commitment. The flag does not describe the complete system-wide speculation policy or the overhead borne by other processes.

The threat SML closes: an attacker who has unprivileged code running on the same machine (or in some configurations, even on a different machine sharing the same CPU) using speculative-execution timing side channels to extract data from a victim process. SML prevents the process from disabling the documented protection; it does not establish that every side channel is eliminated.

## NO_CHILD — Forbid fork and clone

NO_CHILD refuses fork, clone without `CLONE_THREAD`, and other paths that create a new process. `CLONE_THREAD` operations that add threads to the current process are not covered. It constrains subsequent creation; it does not remove children that already exist.

With NO_CHILD enabled:

- `fork()` returns `-EPERM`.
- `clone()` returning a new process returns `-EPERM`.
- `clone3()` with similar flags returns `-EPERM`.

The threat closed: an exploit that has gained code execution in the process attempting to spawn a helper process to do its work. NO_CHILD makes that path impossible — the process is locked into being a single process; whatever the attacker does, they cannot fork out of it.

NO_CHILD is appropriate for processes that fundamentally do not need to fork. Many long-lived services (a single-process event-loop daemon, for example) never call fork in their normal operation. Setting NO_CHILD on such a service costs nothing operationally and closes a frequently-abused exploitation path.

Services that *do* fork during their operation (a classical Unix `accept`-fork-handle server) cannot use NO_CHILD. Either restructure the service to use threads or async I/O, or accept that NO_CHILD does not fit.

NO_CHILD does not prevent threads in the same process — `pthread_create` and its kin are CLONE_THREAD-style operations and remain available. The mitigation is specifically about new processes, not new threads.

## UI_ACCESS — Reserved

`UI_ACCESS` (0x010) is reserved. The Kernel TRM describes its intended purpose as interaction with higher-integrity UI elements, for future desktop functionality.

Its presence in the accepted mask or in PSB readback is not evidence of an implemented UI protection. Do not include it as an effective defence in a hardening assessment.

## Combining mitigations

A hardening policy may address several independent needs:

- **WXP** — no writable-executable pages
- **LSV** — only signed libraries
- **TLP** — only libraries from approved paths
- **CFIF** and **CFIB** — forward and backward control-flow models, subject to the activation limits above
- **PIE** — ASLR-aware binaries
- **NO_CHILD** if applicable — no child processes

Plus possibly **SML** for secrets-handling processes.

These address different exploitation paths, but a policy must account for both compatibility and support. The current Kernel TRM's unavailable CFIF, self-only CFIB and empty production TLP cache prevent treating the list as a deployable default. Compare the service's required set with successful application and committed readback, not with an idealised list.

The `ALL` mask (0x3FF) identifies valid request bits. It is useful for input validation, not blanket hardening: it includes reserved and unavailable flags. Because requests are all-or-nothing, an unavailable requested protection prevents the whole request from committing. Do not substitute ALL for a reviewed set or silently omit a required protection to make a request succeed.

## What mitigations don't help with

A few clarifications worth pinning:

- **Mitigations do not protect against logic bugs.** A process that has been tricked into doing something its code is allowed to do but should not (a misconfigured permission check, a misused API) is not protected by mitigations.
- **Mitigations do not protect against bugs in the kernel.** A kernel exploit operates above the mitigation layer; mitigations are kernel-enforced, and a compromised kernel can disable them.
- **Mitigations do not protect against bugs in the language runtime that bypass them.** A JIT that legitimately needs writable-executable pages is incompatible with WXP; running it with WXP either disables the JIT (which may fail in unexpected ways) or refuses to set WXP at all.
- **Mitigations do not catch all exploits.** They are layered defences. An exploit that fits within one mitigation's blind spot (a JIT spray attack against a non-WXP process, say) succeeds despite the other mitigations being on. Defence in depth is the goal — the more layers, the more an exploit must defeat.

## See also

- [Process mitigations](~peios/process-mitigations/overview) — the model these flags share.
- [Applying and lifecycle](~peios/process-mitigations/applying-and-lifecycle) — setting the flags and how they propagate.
- [Binary signing](~peios/binary-signing/overview) — the signatures LSV verifies against.
