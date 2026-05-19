---
title: Catalog
type: concept
description: Peios defines eight active process mitigations in v0.20 — LSV, WXP, TLP, CFIF, CFIB, PIE, SML, NO_CHILD — plus a reserved UI_ACCESS slot. This page covers each one in turn — what it does, which kernel surface it gates, what it blocks, and when to enable it.
related:
  - peios/process-mitigations/overview
  - peios/process-mitigations/applying-and-lifecycle
  - peios/binary-signing/overview
---

There are eight mitigations active in v0.20 plus a reserved slot. This page covers each one. Every mitigation works the same way structurally — a flag on the PSB; the kernel checks the flag at the syscall layer; offending operations are refused — but each gates a different kind of operation. Understanding the catalog is understanding which threats each closes off.

## LSV — Library Signature Verification

LSV is the mitigation that decides which executable code may be loaded into the process from disk. With LSV enabled, `mmap(PROT_EXEC)` requires that the file backing the mapping carry a valid signature whose PIP trust level is at least the calling process's `pip_trust`. Unsigned files cannot be loaded executable; files signed at a lower trust level cannot either.

The kernel's behaviour:

- When `mmap(..., PROT_EXEC, ...)` is called on a file fd, the kernel checks the file's signature.
- If the file has no signature, or its signature is invalid, the call fails with `-EACCES`.
- If the file's signature is valid but its PIP trust level is below the calling process's, the call also fails with `-EACCES`.
- If the file's signature is valid and at sufficient trust, the call proceeds.

The result: a TCB process (`pip_trust = 8192`) can only load TCB-signed libraries. A future App-signed process (`pip_trust = 2048`) could load App-signed or higher libraries but not Authenticode-signed or unsigned ones. A None-trust process is not subject to LSV (LSV does not check against None; the process can load anything).

LSV is the mitigation that closes the "load arbitrary shared object" injection path. An attacker who has overwritten a function pointer in the process to point at `dlopen("evil.so")` finds that the call fails — the kernel refuses to map the unsigned library as executable.

LSV is appropriate for any PIP-protected process. peinit, authd, and the rest of the TCB all run with LSV enabled.

## WXP — Write-XOR-Execute

WXP refuses any operation that would transition a memory page from writable to executable. Pages can be writable, or executable, but not both at any moment, and not become executable having been writable.

Specifically:

- `mmap(..., PROT_WRITE | PROT_EXEC, ...)` is refused if WXP is enabled.
- `mprotect(addr, len, PROT_EXEC)` on pages previously protected with PROT_WRITE is refused.
- `mprotect(addr, len, PROT_WRITE)` on pages previously protected with PROT_EXEC is refused.

The check fires per-page. The kernel tracks the protection history of each mapping; a page that has ever been writable cannot subsequently be made executable, and vice versa.

The effect: JITs (Just-In-Time compilers) cannot run with WXP enabled. A JIT's whole job is to allocate a region of writable memory, generate code into it, then flip the region executable — exactly what WXP refuses. Binaries that need this flexibility (managed-language runtimes, dynamic-recompilation engines) cannot be hardened with WXP.

Binaries that do not generate code at runtime are unaffected. A normal native binary loads its code from disk at exec (PROT_EXEC granted by exec, not by mprotect), uses stack and heap as PROT_READ | PROT_WRITE, and never needs to flip pages between write and execute. WXP is invisible to such binaries.

WXP is one of the cornerstones of process hardening. It closes the "inject shellcode and jump to it" pathway: an attacker who has corrupted memory cannot make their corrupted region executable. The exploit's payload, no matter how big, is just data.

## TLP — Trusted Library Paths

TLP gates which directories executable mappings may come from. The kernel maintains a per-system cache of approved directory prefixes (populated from the registry at boot); when TLP is enabled, a process can only `mprotect(PROT_EXEC)` (or `mmap(PROT_EXEC)`) a region backed by a file whose resolved absolute path begins with one of those prefixes.

The check:

- The kernel resolves the file's path to an absolute pathname.
- The absolute path is compared against each entry in the TLP cache.
- If the path begins with any entry's prefix, the operation proceeds.
- If not, the operation fails with `-EACCES`.

The TLP cache holds typical system library paths: `/usr/lib/`, `/lib/`, perhaps a few service-specific paths. Anything in `/tmp/`, `/home/`, or in directories not explicitly in the cache is excluded.

The threat TLP closes is "load executable code from a writable directory". A code-injection attack that writes a shared object into `/tmp/` and loads it via dlopen finds the load refused — `/tmp/` is not in the TLP cache. The same attack that puts the file in `/usr/lib/` is much harder; non-administrators cannot write to `/usr/lib/` in a standard configuration.

TLP composes naturally with LSV. LSV says "the library must be signed at sufficient trust"; TLP says "the library must come from an approved location". Both are typically enabled together on hardened processes; either alone is a useful but partial defence.

TLP cache details:

- Maximum 64 entries.
- Each entry is a UTF-8 absolute directory prefix, beginning and ending with `/`.
- Maximum 4096 bytes per path.
- Populated by peinit at boot from the registry. The cache is machine-wide; every process sees the same prefixes.

## CFIF and CFIB — Control Flow Integrity (Forward and Backward)

CFIF (Forward) and CFIB (Backward) are the two halves of control-flow integrity. They are separate flags so a process can enable one without the other, though most hardened processes enable both. The combined effect is to refuse any indirect branch (forward or return) that lands at an unintended target.

The legacy flag `CFI` (0x008) is an alias that sets both CFIF and CFIB. Modern code should set CFIF (0x040) and CFIB (0x080) directly; the alias exists for compatibility.

### CFIF — Forward CFI

CFIF refuses indirect calls and jumps (function pointers, vtables) that land at an instruction other than a designated call target. On x86_64, the hardware mechanism is IBT (Indirect Branch Tracking) — every legitimate target of an indirect branch is marked with an `ENDBR64` instruction; an indirect branch landing somewhere without `ENDBR64` traps.

With CFIF enabled, the kernel ensures the process runs in IBT-enforcing mode. An indirect branch to a non-`ENDBR64` target generates a control-protection fault, which the kernel turns into a fatal signal to the process.

The threat closed: ROP/JOP (Return-Oriented / Jump-Oriented Programming) attacks that chain together short "gadgets" found in legitimate code. The gadgets are short sequences ending in `ret` or indirect jump; without CFIF, an attacker can use them to perform arbitrary operations. With CFIF, the gadgets are no longer reachable because the indirect branch into them lands somewhere without `ENDBR64`.

### CFIB — Backward CFI

CFIB refuses `ret` instructions that do not return to the address pushed by the corresponding `call`. The hardware mechanism is the shadow stack — a separate stack maintained by the CPU that records return addresses. Every `call` pushes onto both the data stack and the shadow stack; every `ret` pops both and compares them. A mismatch traps.

With CFIB enabled, the kernel ensures the process runs with the shadow stack engaged. An attacker who overwrites a return address on the data stack cannot get the `ret` to honour their overwrite — the shadow stack still has the original address; the comparison fails; the process dies.

The threat closed: classic ROP. Overwriting return addresses is the foundation of return-oriented exploitation; CFIB makes the trick impossible (or, more precisely, makes it lead to immediate process termination instead of attacker-chosen execution).

Both CFIF and CFIB require hardware support (Intel CET, ARM BTI/PAC, etc.) plus binary support (the binary must have been compiled with the relevant flags). Enabling CFIF or CFIB on a process whose binary does not support it has no effect — the kernel can only enforce what the hardware can detect.

## PIE — Position-Independent Executable

PIE refuses exec of binaries that are not position-independent. The kernel checks the binary's ELF flags at exec; if PIE is enabled on the parent process's PSB and the new binary is not PIE-built, the exec fails with `-EACCES`.

PIE-built binaries are loaded at randomised addresses every time they exec — Address Space Layout Randomisation (ASLR) covers the executable's own segments, not just the heap and shared libraries. An attacker who would have needed to know the address of a specific instruction in the binary to construct a ROP chain finds the address randomised and unpredictable.

A non-PIE binary has fixed addresses for its code and globals. Every exec puts them in the same place. An attacker can compute exploitation gadget addresses once and reuse them across runs.

PIE is the easiest mitigation to enable: any modern compilation with `-fPIE -pie` produces a PIE binary. Distributions of Peios produce PIE binaries by default. The mitigation simply refuses to exec the rare exception.

The cost: a small (single-digit-percent) performance overhead because PIE binaries reference memory through GOT/PLT tables rather than direct addresses. The cost is dwarfed by the security benefit on any modern CPU.

## SML — Speculation Mitigation Lock

SML enables the most paranoid set of speculative-execution mitigations for the process — Spectre, Meltdown, MDS, and the rest of the side-channel family. With SML enabled, the kernel applies all relevant mitigations on every context switch into and out of this process: indirect-branch barriers, store buffers cleared, microcode flushes, anything the CPU supports for spectre-class defences.

The cost is significant — depending on the CPU and the workload, anywhere from a few percent to tens of percent of performance. Most workloads do not need it. The processes that do need it are the ones handling secrets that an attacker on the same machine could otherwise extract through speculative-execution side channels: cryptographic key holders, sealed-secret stores, the TCB processes that hold sensitive material.

SML is per-process. A SML-enabled process pays the cost; processes without SML in the same kernel use the default (lighter) set of mitigations.

The threat SML closes: an attacker who has unprivileged code running on the same machine (or in some configurations, even on a different machine sharing the same CPU) using speculative-execution timing side channels to extract data from a victim process. Without SML, the standard mitigations may be enough for most attacks; with SML, the process is hardened against even the most subtle.

## NO_CHILD — Forbid fork and clone

NO_CHILD refuses fork, clone, and any other path that would create a new process or new thread sharing the current address space. (CLONE_THREAD-style clones to add threads to the current process are *not* covered by NO_CHILD; the flag only refuses *new processes*.)

With NO_CHILD enabled:

- `fork()` returns `-EPERM`.
- `clone()` returning a new process returns `-EPERM`.
- `clone3()` with similar flags returns `-EPERM`.

The threat closed: an exploit that has gained code execution in the process attempting to spawn a helper process to do its work. NO_CHILD makes that path impossible — the process is locked into being a single process; whatever the attacker does, they cannot fork out of it.

NO_CHILD is appropriate for processes that fundamentally do not need to fork. Many long-lived services (a single-process event-loop daemon, for example) never call fork in their normal operation. Setting NO_CHILD on such a service costs nothing operationally and closes a frequently-abused exploitation path.

Services that *do* fork during their operation (a classical Unix `accept`-fork-handle server) cannot use NO_CHILD. Either restructure the service to use threads or async I/O, or accept that NO_CHILD does not fit.

NO_CHILD does not prevent threads in the same process — `pthread_create` and its kin are CLONE_THREAD-style operations and remain available. The mitigation is specifically about new processes, not new threads.

## UI_ACCESS — Reserved

`UI_ACCESS` (0x010) is reserved in v0.20. The intended use is for processes that interact with the user interface in privileged ways; the mitigation, when defined, will restrict what UI surfaces the process may attach to.

In v0.20 the flag has no effect — setting it is allowed but does nothing. Future versions may define behaviour.

## Combining mitigations

Most hardened processes enable multiple mitigations. A typical TCB daemon's mitigation set in v0.20:

- **WXP** — no writable-executable pages
- **LSV** — only signed libraries
- **TLP** — only libraries from approved paths
- **CFIF** + **CFIB** — control-flow integrity
- **PIE** — ASLR-aware binaries
- **NO_CHILD** if applicable — no child processes

Plus possibly **SML** for secrets-handling processes.

The mitigations compose orthogonally — each one closes a different attack pathway. WXP closes shellcode injection; LSV closes signed-library-only-rule; TLP closes load-from-writable-directory; CFI closes ROP/JOP; PIE closes fixed-address attacks; NO_CHILD closes process-spawning escapes; SML closes speculative-execution side channels. A process with all of them is meaningfully harder to exploit than one with any subset.

The `ALL` flag (0x3FF) is shorthand for "enable every defined mitigation". A process that wants the strictest possible hardening can set ALL in one call.

## What mitigations don't help with

A few clarifications worth pinning:

- **Mitigations do not protect against logic bugs.** A process that has been tricked into doing something its code is allowed to do but should not (a misconfigured permission check, a misused API) is not protected by mitigations.
- **Mitigations do not protect against bugs in the kernel.** A kernel exploit operates above the mitigation layer; mitigations are kernel-enforced, and a compromised kernel can disable them.
- **Mitigations do not protect against bugs in the language runtime that bypass them.** A JIT that legitimately needs writable-executable pages is incompatible with WXP; running it with WXP either disables the JIT (which may fail in unexpected ways) or refuses to set WXP at all.
- **Mitigations do not catch all exploits.** They are layered defences. An exploit that fits within one mitigation's blind spot (a JIT spray attack against a non-WXP process, say) succeeds despite the other mitigations being on. Defence in depth is the goal — the more layers, the more an exploit must defeat.
