---
title: PIP in practice
type: concept
description: PIP has a handful of practical interactions that are not obvious from the model alone — its asymmetry with impersonation, why peinit ends up as the lifecycle manager for PIP-protected processes, how it differs from MIC, what its threat-model ceiling is, and the limitations of the v0.20 implementation. This page covers each.
related:
  - peios/process-integrity-protection/overview
  - peios/process-integrity-protection/the-process-security-descriptor
  - peios/process-integrity-protection/the-two-check-rule
  - peios/access-decisions/mandatory-integrity-control
  - peios/impersonation/the-two-gates
  - peios/binary-signing/overview
---

The PIP model is small once you have the dominance rule and the two-check rule in hand. But the practical consequences of those two rules ripple outward in ways that are not obvious from the rules themselves. PIP's asymmetric relationship with impersonation; the operational pattern that ends up forcing peinit to be the lifecycle manager for every PIP-protected process; the contrast with MIC; the threat-model ceiling above which PIP simply does not protect; and the v0.20 limitations of the implementation.

This page covers each.

## PIP and impersonation

PIP reads the **PSB**, not the effective token. Impersonation changes the effective token; it does not change the PSB. The consequence: impersonating a high-trust identity does **not** raise a process's PIP level.

A worked example. A user-mode application — `pip_type = None` — accepts a connection from a TCB daemon. The TCB daemon connected at Delegation level. The application calls `kacs_impersonate_peer` and now has the TCB daemon's identity installed as its effective token. The token is at SYSTEM integrity, with TCB-flavoured group memberships, with many privileges enabled.

What can the application now do?

- Access checks that use the **effective token** (file access, registry access, regular DACL evaluation) succeed with the TCB daemon's authority. The application can open TCB-only files.
- Access checks that use the **PSB** (PIP dominance for cross-process operations) still see the application's None-level PSB. The application cannot signal or debug TCB daemons — its PIP did not change.

The asymmetry is deliberate. PIP is a property of the binary running, not of who the binary is acting as. Allowing impersonation to raise PIP would let any service that ever accepts a TCB-level client effectively become TCB-level for the duration. The model is built on the idea that the binary is what is trusted, and a binary cannot lend its trust through impersonation.

The same asymmetry applies in reverse: if a TCB daemon impersonates a user-mode client (rare; usually it just acts as them at the file-access level), the TCB daemon's PSB is still TCB-level. The impersonation does not lower its PIP.

## MIC vs PIP

PIP and MIC look superficially similar — both compare a numeric level on the caller against a level on the object, both block when the caller is below. The two diverge in several ways that matter.

| | MIC | PIP |
|---|---|---|
| What it labels | Tokens (`integrity_level`) | Processes (`pip_type`, `pip_trust`) on the PSB |
| What it reads at access time | Effective token (impersonation-visible) | PSB (impersonation-invisible) |
| Axes | 1 (integrity level) | 2 (type and trust) |
| Default | Medium with `NO_WRITE_UP` for unlabelled objects | None — objects are PIP-unrestricted unless they opt in via a label ACE |
| Bypassed by privileges? | Privilege-granted bits survive | **No** — privilege-granted bits are revoked for non-dominant callers |
| Default policy | Block writes from below | Only the rights in the trust-label ACE's mask are permitted; everything else is denied |

The two layers complement each other. MIC is the integrity axis for token-driven access (where impersonation matters); PIP is the trust axis for process-driven access (where the binary matters). An access can be blocked by either, or allowed by both.

The most consequential difference is the privilege handling. MIC respects privilege grants; PIP does not. A backup tool with `SeBackup` granted to it can read across MIC boundaries (read a higher-integrity file) because privileges preserve bits through MIC. The same backup tool **cannot** read across PIP boundaries — `SeBackup` does not grant the read on a PIP-protected object if the caller does not dominate. The privilege grant is stripped at the PIP check.

This is the security model's load-bearing assertion: privileges are not enough. A privileged but untrusted binary cannot bypass PIP-protected objects.

## peinit as the lifecycle manager

A PIP-protected process can only be signalled by a process that PIP-dominates it. For the TCB daemons — Protected/8192 — that means the signalling process needs at least Protected/8192. Which means it needs to be a TCB-signed binary itself.

In practice, the only process that fits this description and exists for the express purpose of managing other processes is **peinit**. peinit is signed at TCB level, runs at PIP Protected/8192, and is the system's init-equivalent.

The consequence: every PIP-protected process's lifecycle — start, restart, shutdown — flows through peinit, because no other binary can send the relevant signals. An ordinary administrator cannot use `systemctl stop authd` (or its Peios equivalent) directly; they ask peinit to do it. Even SIGTERM from a shell would be denied if the shell is not PIP-dominating.

This is the lifecycle manager pattern. It is not enforced by a specific kernel mechanism (peinit is not "marked" as the lifecycle manager); it falls out naturally from the PIP rule. peinit happens to be the only thing that can talk to TCB processes.

Practical implications:

- Tooling that interacts with the TCB sends commands to peinit, not directly to the TCB processes.
- Restart loops are implemented in peinit. If a TCB daemon crashes, peinit is the entity that decides whether and how to restart it — no external supervisor can.
- Service-management tools for non-TCB services can be more direct, because non-TCB processes are not PIP-protected and ordinary signal-sending works.

## Privileges and PIP, in detail

The relationship between privileges and PIP comes up enough to be worth pinning. The general rule: **privileges do not bypass PIP**. The specific cases:

- **`SeDebugPrivilege`**: bypasses the SD check on cross-process operations. Does **not** bypass PIP. A privileged debugger can attach to any user-mode process; it cannot attach to TCB processes.
- **`SeBackupPrivilege` / `SeRestorePrivilege`**: grants read/write bits through AccessCheck. Bits granted by these privileges are subject to PIP — a non-dominant caller has them stripped during the PIP check for PIP-protected objects. (The grant happens at step 4 of AccessCheck; the PIP strip happens at step 5.)
- **`SeImpersonatePrivilege`**: lets a service impersonate clients. Does not affect PIP; the PSB stays the same. The impersonated token may carry MIC at a higher level (capped by the integrity ceiling), but PIP does not move.
- **`SeTakeOwnershipPrivilege`**: grants `WRITE_OWNER` regardless of DACL. Subject to PIP — a non-dominant caller cannot take ownership of a PIP-protected object even with the privilege.
- **`SeTcbPrivilege`**: gates TCB operations (token creation, mount-policy administration). Held only by TCB processes anyway, which are PIP-dominant by virtue of their signing. The privilege does not extend PIP authority.

In short: every privilege the catalog defines operates within PIP, not above it. There is no privilege that bypasses PIP. The trust ceiling is absolute from the privilege model's perspective.

## The threat-model ceiling

PIP's protection is bounded by what the kernel can enforce. Specifically:

- **A compromised kernel voids PIP.** If an attacker has code running in the kernel (e.g., via a malicious or buggy kernel module), they can read PSBs directly, modify memory directly, and bypass every PIP check. The defence against this is `CONFIG_MODULE_SIG_FORCE=y` — only signed kernel modules are accepted — but that defence is itself a precondition for PIP being meaningful.
- **Hardware DMA bypasses PIP.** A device that can perform DMA can read or write any physical memory. The defence is IOMMU configuration, which is a kernel concern, not a PIP concern.
- **`/dev/mem` access bypasses PIP if writable.** Even reading `/dev/mem` gives access to physical memory. The defence is `CONFIG_STRICT_DEVMEM=y`, which restricts `/dev/mem` to I/O regions only.
- **PIP does not provide cryptographic memory isolation.** Two PIP-protected processes share the same physical memory and the same kernel. PIP is logical, not cryptographic; a kernel compromise sees through it.

These are not bugs in PIP — they are the kernel's responsibility, sitting above the PIP layer. PIP is the right defence for "a buggy user-mode application that an attacker is running"; it is not the right defence for "an attacker who has kernel code execution".

For a deployment where the threat model includes kernel-code attackers, PIP is insufficient on its own and must be paired with hypervisor-style isolation. That is a Peios-v2 concern, not a PIP concern.

## What v0.20 does not do

A handful of PIP limitations specific to v0.20 are worth knowing:

- **No per-binary revocation.** A signed binary later found malicious cannot be invalidated short of removing it from the filesystem or replacing the kernel's signing key catalogue. There is no hash-based revocation list.
- **The Isolated PIP type is reserved.** `pip_type = 1024` is documented and present in the model but no v0.20 signing key targets it. No binary will have this type until a future version defines its use.
- **Scripts are not signed.** A script's PIP comes from its interpreter, not the script itself. A signed TCB interpreter running an untrusted script runs the untrusted code at TCB level. This is why interpreters are not signed at TCB unless the script content is itself trusted.
- **Only one signing key in v0.20 (the TCB key).** Lower-trust tiers (App, Authenticode) are reserved in the catalogue but no key exists for them in v0.20. All signed binaries on a v0.20 system are TCB binaries. App-level and Authenticode-level signing is future work.
- **PIP visibility in `/proc`.** PIDs and directory names remain visible in `/proc` `getdents()` listings regardless of PIP — the kernel reveals that processes exist, even when their data cannot be read. Only file access within `/proc/<pid>/` is gated. A future version may filter directory listings as well.
- **Coredumps are disabled for PIP-protected processes.** A PIP-protected process's coredump is a potential secret leak; the kernel sets dumpability to false at exec and refuses to re-enable it via `prctl(PR_SET_DUMPABLE, 1)` while `pip_type != None`. The defence is mandatory.

These are limitations of the implementation, not the model. The model accommodates revocation, additional types, signed scripts, and richer visibility filtering; they just aren't there yet.

## When PIP is the right tool

A few patterns where PIP is the answer:

- **Protecting kernel-adjacent daemons.** authd, loregd, eventd, and other TCB components must not be reachable by ordinary user code, even by administrators. PIP is the layer that enforces this. Their signing at TCB level produces processes that no non-TCB caller can interfere with.
- **Anti-malware tools that need to be hard to disable.** A security daemon signed at the AntiMalware tier (`pip_type = Protected`, `pip_trust = 1536` in the catalogue) is protected against attempted disablement by malware running at lower trust.
- **Cryptographically signed third-party services that need protection from local administrators.** A licensed-software service whose vendor has signed it at the App or Authenticode tier can be configured to refuse modification by anyone other than at the same or higher tier.

And patterns where PIP is **not** the answer:

- **Sandboxing untrusted code.** PIP protects high-trust processes from low-trust ones, not the other way around. To restrict what an untrusted process can do, use confinement or restricted tokens.
- **Authorising users for specific operations.** PIP is about binaries; identity-based authorisation is the DACL's job.
- **Network access control.** PIP does not gate network operations; nftables, the network stack, and the SDs on network endpoints do.

The cleanest mental check: ask "is the policy I want to express about *what kind of program* may do this?". If yes, PIP. If it is about *who* may do this, the DACL is the answer.
