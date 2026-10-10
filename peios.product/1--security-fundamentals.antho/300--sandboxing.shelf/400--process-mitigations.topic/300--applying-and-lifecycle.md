---
title: Applying and lifecycle
type: concept
description: Read committed mitigation state, distinguish requests from active protection, and understand the one-way lifecycle and activation failures.
related:
  - peios/process-mitigations/overview
  - peios/process-mitigations/catalog
  - peios/process-integrity-protection/overview
  - peios/process-integrity-protection/the-two-check-rule
  - peios/tokens/overview
  - peios/peiosutils/system-and-processes/logonse
  - peios/sdk-processes/process-h
---

A requested mitigation mask is not evidence that the process is protected. Check the application's or launcher's result, then read the **committed mitigation state** of the process that is actually running. A service's intended policy, a flag's presence in the catalog, and a successful activation are different things.

For an operator investigating hardening:

1. Identify the process and read it with `logonse psb --pid PID`, replacing `PID` with the target's process ID. With only `--pid`, this is a read-only inspection; see the [logonse reference](~peios/peiosutils/system-and-processes/logonse#logonse-psb).
2. Record the reported mitigations and process GUID alongside the service's required policy and any application error. The GUID distinguishes a replacement process from an earlier process with the same PID.
3. Compare the committed flags with the required set and the [activation limits](~peios/advanced-peios/peios-kernel/kacs/process-security-block/fields#process-mitigations-one-way). If a required flag is absent, or the report is refused or unavailable, do not treat the intended protection as verified.
4. After an authorised launch or hardening change, check the result and read the same process again. Verify a new process separately after a restart; do not carry an old process's result forward.

This page explains the lifecycle and the limits of that evidence. Application code belongs in the [SDK hardening guide](~peios/sdk-access-control/hardening-a-process) and [`process.h` reference](~peios/sdk-processes/process-h); command syntax belongs in [logonse](~peios/peiosutils/system-and-processes/logonse). The Kernel TRM describes activation-backed behaviour and current implementation limits below. Use the documentation for the deployed release when checking support; this page does not establish when those implementation limits changed between releases.

## Requests and committed protection

`kacs_set_psb` is the kernel operation behind a mitigation request. It targets a process by pidfd and takes a mask of `KACS_MIT_*` flags. The [SDK reference](~peios/sdk-processes/process-h#setting-mitigations) documents the callable wrapper, including `-1` for the calling process; the [kernel ABI](~peios/advanced-peios/peios-kernel/kacs/kacs-abi#process-mitigation-bits) holds the complete numeric flag table and syscall declaration.

A request is **additive and one-way**. It cannot clear an existing flag. Requesting an already-set flag or a subset of the committed set does not remove or weaken earlier protections. `CFI` is a legacy request alias for `CFIF | CFIB`; the alias itself is not retained in the committed bitfield. `UI_ACCESS` is reserved. `ALL` is the valid-bit mask, not a recommended policy or a promise that every defined flag can be activated.

The [Kernel TRM](~peios/advanced-peios/peios-kernel/kacs/process-security-block/fields#process-mitigations-one-way) specifies **activation-backed, all-or-nothing** application: before committing a new flag, the kernel activates its protection or verifies the required invariant. If any requested mitigation cannot be activated or verified, no bits from that request are changed. Bits committed by earlier successful requests remain set.

Unknown bits and an invalid or unauthorised target can be refused. Valid bits can also be refused because of existing mappings, platform support, or the activation route. A request made by the process itself is subject to these checks too.

## Self versus another process

**Self-application** needs neither `PROCESS_SET_INFORMATION` on another process nor PIP dominance over one. A thread can request hardening for its own process. This is permission to tighten its constraints, not an unconditional promise of success: activation and input validation still have to succeed.

**Applying mitigations to another process** requires both:

- `PROCESS_SET_INFORMATION` on the target's process security descriptor.
- PIP dominance over the target, under the [two-check rule](~peios/process-integrity-protection/the-two-check-rule).

Satisfying both gates does not make every mitigation available remotely. The Kernel TRM documents `CFIB` activation as **self-only**: enabling it on a task other than the caller fails. It also documents `CFIF` activation against a live task as unconditionally returning `ENODEV`, because there is no userspace IBT/BTI control surface. A supervisor cannot overcome these activation limits merely by having authority over the target.

For a launcher using this pattern, distinguish the parent's code **running in the freshly forked child** from a parent targeting another process's pidfd. Both are possible application contexts, but only the former is self-application. Do not infer that a requested service policy was applied from the launcher's identity alone.

The source descriptions differ on peinit: the Kernel TRM calls between-fork-and-exec setting typical, while the [peinit account](~peios/boot-and-trust-establishment/peinit-pid-1) says it does not apply per-service mitigation flags this way. The generic lifecycle pattern does not establish current peinit behavior or a release transition. Verify the running service's committed state.

## Where in the process lifecycle

A process can request additional mitigations during its life, but when it requests them changes what must be validated and what events they can constrain:

- **After fork, before exec.** The launcher's code running in the child can request hardening before loading the service binary. The launcher must handle a failed request rather than assume the child is hardened.
- **At the binary's entry point.** The program can request compatible protections early, before processing untrusted input, and check the result.
- **After early-stage initialisation.** This works only if the protection can be activated over the state already present. Finishing incompatible work first does not exempt its remaining mappings from validation.

The Kernel TRM specifically requires checks of **existing state** for runtime memory mitigations:

| Newly requested protection | Existing state that prevents activation |
|---|---|
| WXP | A writable-and-executable mapping, or another observable violation of the invariant. |
| TLP | A file-backed executable mapping with a missing or unresolvable path, a path outside the approved cache, or another TLP denial. |
| LSV | A file-backed executable mapping with missing, invalid, or insufficiently trusted signing material. |

Anonymous executable mappings are governed by WXP; TLP and LSV apply to file-backed mappings. Architecture-backed CFIF, CFIB and SML must also be made effective for the target or the request fails closed. SML can instead be satisfied when the platform reports speculation as unconditionally not affected.

Do not treat late WXP application as leaving an existing writable-executable region exempt, or late TLP/LSV application as approving libraries already loaded from disallowed paths or without acceptable signatures. The documented response is refusal of the request, not automatic repair of the process. A JIT or startup code generator needs compatibility review; there is no general “generate code first, then set WXP” recipe.

Two restrictions are **event-gated**: PIE governs subsequent exec, and NO_CHILD governs subsequent process creation. Set them before the event they must constrain. Neither retrospectively changes the running binary or removes children that already exist.

## Fork: inheritance

At fork, the child inherits the parent's committed mitigation flags. It cannot remove them. It receives its own process GUID, so inspect the child as a distinct process instance.

If WXP is set, it is inherited. If NO_CHILD is set, the process cannot fork a child in the first place. Creating a thread with `CLONE_THREAD` shares the process's PSB rather than copying it; the same committed mitigation state applies to threads in that process. See [PSB Lifecycle](~peios/advanced-peios/peios-kernel/kacs/process-security-block/lifecycle).

## Exec: preserved flags and compatibility

Exec replaces the binary and address space, but it does not provide an escape from committed mitigations:

- Exec normally keeps the primary identity token, but `NEW_PROCESS_MIN` can replace it with a lower-integrity copy when the executable has an explicit lower integrity label. Thread impersonation is reverted at exec. See [Token lifecycle](~peios/security-fundamentals/tokens/lifecycle#fork-exec-and-the-primary-token).
- PIP fields are recomputed from the new binary's signature.
- The process security descriptor is preserved by exec; explicit descriptor or primary-token changes have their own rules.
- Mitigation flags and the process GUID are **preserved**.

The important exec-specific restriction is **PIE**. If PIE is set and the new binary is not position-independent, exec is refused with `EACCES`. Updating a service to a non-PIE build can therefore prevent its next start. Treat an emergency rebuild that lost PIE support as a compatibility failure to investigate, not a reason to assume the old policy has disappeared.

Preservation does not guarantee that another binary will start or work correctly under the remaining mitigations. A JIT or self-modifying program may need operations WXP refuses; executable library mappings may fail TLP or LSV checks. Do not diagnose every launch failure as PIE merely because it is the explicit exec-gated flag. Review the failing operation and the [catalog](~peios/process-mitigations/catalog).

## NO_CHILD and the lifecycle interaction

Once NO_CHILD is committed, the process cannot fork or clone a new process. A service that needs startup workers must create them before it successfully commits this restriction. Those existing workers have their own inherited state; applying NO_CHILD later to the parent does not retroactively apply it to them.

A server that forks on demand cannot use NO_CHILD during that phase. The flag still permits exec, which replaces the binary in the same process, and `CLONE_THREAD`, which adds a thread rather than a process. See the [NO_CHILD catalog entry](~peios/process-mitigations/catalog#no-child-forbid-fork-and-clone).

## Querying mitigations

Use the read-only `logonse psb --pid PID` form above, or the documented text surface `/proc/<pid>/psb`. A PSB report contains `pip_type`, `pip_trust`, the committed `mitigations` bitfield, and `process_guid`. It does not contain the process security descriptor or the token; those are separate inspection surfaces.

A process can read its own PSB without an access check. Reading another process's PSB needs `PROCESS_QUERY_LIMITED` on its descriptor, **not PIP dominance**. The Kernel TRM also documents `SeDebugPrivilege` rescuing a descriptor denial; acquiring or enabling privileges is not a required diagnostic step. A refused report is incomplete evidence, not proof that the target has no mitigations.

Readback shows what is committed, not the mask a caller merely requested. The CFI alias is not retained; NO_CHILD is part of the same bitfield and UI_ACCESS remains reserved. PIE in that report constrains subsequent exec; it does not prove that the already-running binary was checked at a prior exec. Likewise NO_CHILD does not establish that the process has never created children.

For the format, access rules and software reader, see [Reading the PSB](~peios/advanced-peios/peios-kernel/kacs/process-security-block/fields#reading-the-psb) and [`process.h`](~peios/sdk-processes/process-h#reading-a-psb). Record the process GUID when comparing reports across restarts or correlating events, since PIDs can be reused.

## What happens at process exit

The process's PSB and its flags disappear at exit. A new process starts with what it inherits from its parent, plus whatever its launch path or its own code successfully adds. The binary's filename does not carry a saved mitigation policy.

Launchers therefore need to handle the required policy on every launch, and a self-hardening binary needs to check its own requests regardless of who launched it. Neither arrangement guarantees success simply by making a request. If a required protection is unavailable, the launch or application must treat that as a hardening failure rather than continue under a false assumption. Recheck the replacement process instead of reusing the old process's report.

## Errors

Keep the application's exact error and target context. Distinguish input and authority failures from activation failures; a valid request by an authorised caller can still fail.

| Error reported for a request | What to investigate |
|---|---|
| `EBADF` | Invalid pidfd. |
| `ESRCH` | The target process has exited. |
| `EACCES` | A denied `PROCESS_SET_INFORMATION` check when targeting another process; inspect the reported failure rather than assuming all denials have this cause. |
| `EPERM` | Missing PIP dominance when targeting another process. |
| `EINVAL` | Unknown flag bits in the requested mask. |
| `ENODEV` | The Kernel TRM specifies this unconditionally for CFIF activation against a live task. |

This is not an exhaustive activation-error catalog. Existing mapping incompatibilities, unavailable architecture support and CFIB's self-only restriction must also be considered. The [SDK reference](~peios/sdk-processes/process-h#setting-mitigations) returns `-1` with `errno`; raw kernel errors use the negative error form.

Under the documented all-or-nothing rule, a failed request commits none of that request's bits. Earlier successful commitments remain. Preserve the failure evidence, check the target's committed state, and review the required policy and supported launch path before trying a different request. Do not silently drop a required mitigation or use ALL as a recovery step.

## Where to go next

- [Catalog](~peios/process-mitigations/catalog): what each flag protects and where support or compatibility limits matter.
- [logonse](~peios/peiosutils/system-and-processes/logonse#logonse-psb): existing command reference for PSB inspection and requests.
- [Hardening a process](~peios/sdk-access-control/hardening-a-process): application-side startup and failure handling.
- [PSB Fields](~peios/advanced-peios/peios-kernel/kacs/process-security-block/fields): activation, current implementation limits and readback contract.
- [The two-check rule](~peios/process-integrity-protection/the-two-check-rule): authority required for changes to another process.
