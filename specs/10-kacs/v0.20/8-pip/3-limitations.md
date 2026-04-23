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

## Impersonation interaction

PIP reads from the PSB, not the effective token. When service A (Protected, trust 5) impersonates client B, service A's process isolation checks still use service A's PSB. The client's identity does not affect the process-to-process boundary.

Conversely, if a None-type process impersonates a token that was created for a Protected-type process, the impersonation MUST NOT grant process isolation privileges. The process's PSB is still None.

## Coredumps

When a PIP-protected process crashes, a core dump is a potential secret leak. Core dumps of PIP-protected processes MUST NOT be readable by non-dominant processes.

Two strategies:

**Disable dumps.** Clear the dumpable flag for PIP-protected processes at exec time. No core dump is generated. Simple and secure.

**PIP-protected crash handler.** A signed, high-trust crash handler receives dump data from the kernel and writes it with a restrictive SD that only PIP-dominant processes can read. The kernel generates dump data internally (in the crashing process's own context), so PIP process isolation is never bypassed.

> [!INFORMATIVE]
> Disabling dumps is the minimum viable implementation. A PIP-protected crash handler is the long-term solution that preserves diagnostics. The two are not mutually exclusive.
