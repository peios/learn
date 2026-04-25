---
title: PIP Limitations
---

## Threat model boundary

PIP operates within the kernel's trust boundary. Three things sit outside it:

**Kernel compromise.** A loaded kernel module runs with unrestricted access to all memory and kernel data structures. PIP is enforced by the kernel; if the kernel is compromised, PIP is void. SeLoadDriverPrivilege is therefore the ceiling of PIP's guarantees.

Defense-in-depth:

- `CONFIG_MODULE_SIG_FORCE=y` — require cryptographically signed kernel modules.
- Strip SeLoadDriverPrivilege from all tokens except peinit's.

**Hardware access.** DMA-capable devices can read and write physical memory directly, bypassing the CPU's virtual memory system. IOMMU mitigates this but IOMMU configuration is a kernel responsibility.

**Hypervisor-level isolation.** PIP cannot provide guarantees equivalent to hypervisor-based memory isolation. The threat model ceiling is "non-compromised kernel."

## Fd inheritance across PIP transitions

When a PIP-protected process forks and the child execs an unsigned binary, the child's PIP drops to None. However, file descriptors inherited from the parent retain their cached granted masks — including access to PIP-protected objects that the child could not independently open.

KACS does not perform fd sanitization at PIP transitions. This is an intentional simplification for v0.22. The mitigations are:

- **O_CLOEXEC.** TCB processes SHOULD open all fds with O_CLOEXEC. Fds that don't survive exec cannot leak. Token fds are O_CLOEXEC by default.
- **Operational discipline.** PIP-protected processes (authd, loregd, etc.) are TCB components that should not fork+exec untrusted binaries. Their children are other signed TCB components launched by peinit.
- **`no_child_process`.** TCB processes that have no legitimate reason to fork can set this PSB restriction to prevent the scenario entirely.

Kernel-level fd sanitization at exec-time PIP downgrade (closing fds whose granted masks exceed what the new PIP level would allow) is a future enhancement. The semantics are non-trivial: the kernel would need to walk all fds, re-evaluate PIP eligibility for each, and close those that fail — potentially breaking legitimate fd inheritance patterns.

SCM_RIGHTS fd injection into PIP-protected processes is not a PIP-specific concern. The received fds carry the sender's granted masks (typically lower privilege), and the handle model applies: possession is authorization. This is a general confused-deputy risk, not a PIP bypass.

## Impersonation interaction

PIP reads from the PSB, not the effective token. When service A (Protected, trust 5) impersonates client B, service A's process isolation checks still use service A's PSB. The client's identity does not affect the process-to-process boundary.

Conversely, if a None-type process impersonates a token that was created for a Protected-type process, the impersonation MUST NOT grant process isolation privileges. The process's PSB is still None.

## No debug opt-out

PIP determination is entirely kernel-driven from the binary's cryptographic signature. There is no equivalent of Windows's `PROC_THREAD_ATTRIBUTE_PROTECTION_LEVEL` — a parent process cannot choose to launch a signed binary without PIP protection.

This is intentional: removing the parent-controlled aspect eliminates the attack surface where a compromised launcher forges a protection level. The trade-off is that a signed binary always gets full PIP protection and cannot be ptraced, even for debugging.

**Workaround:** compile an unsigned debug build of the binary. An unsigned binary gets `pip_type = None` and is fully debuggable. This is the intended development workflow — production binaries are signed and protected, debug binaries are unsigned and unprotected. A formal opt-out mechanism may be added in a future version if the operational need is demonstrated.

## Coredumps

When a PIP-protected process crashes, a core dump is a potential secret leak. Core dumps of PIP-protected processes MUST NOT be readable by non-dominant processes.

Two strategies:

**Disable dumps.** Clear the dumpable flag for PIP-protected processes at exec time. No core dump is generated. Simple and secure.

**PIP-protected crash handler.** A signed, high-trust crash handler receives dump data from the kernel and writes it with a restrictive SD that only PIP-dominant processes can read. The kernel generates dump data internally (in the crashing process's own context), so PIP process isolation is never bypassed.

> [!INFORMATIVE]
> Disabling dumps is the minimum viable implementation. A PIP-protected crash handler is the long-term solution that preserves diagnostics. The two are not mutually exclusive.
