---
title: Inspecting processes
type: concept
description: A process's inspectable state spans its token (covered separately), its PSB (PIP fields and mitigation flags), and its process SD. Inspection of another process requires PROCESS_QUERY_INFORMATION on the target plus PIP dominance. This page covers the surfaces and the rules.
related:
  - peios/inspecting/overview
  - peios/inspecting/tokens
  - peios/inspecting/sessions
  - peios/process-integrity-protection/overview
  - peios/process-integrity-protection/the-process-security-descriptor
  - peios/process-mitigations/overview
---

A process's inspectable state spans three things: its **token** (its identity), its **PSB** (its PIP labels and mitigation flags), and its **process SD** (the policy on the process as an object). Each is read through its own surface but the access rules are similar — your own state is always readable; another process's state needs `PROCESS_QUERY_INFORMATION` plus PIP dominance.

This page covers the per-process inspection surfaces beyond the token. Tokens are covered in [Inspecting tokens](~peios/inspecting/tokens); this page is about the PSB and the process SD.

## What the PSB holds

The Process Security Block is the per-process kernel structure with:

| Field | Meaning |
|---|---|
| `pip_type` | The process's PIP type (None / Protected / Isolated). |
| `pip_trust` | The PIP trust level within the type. |
| Mitigation flags | The bitfield of enabled mitigations (WXP, LSV, TLP, CFIF, CFIB, PIE, SML, NO_CHILD, etc.). |
| `security_descriptor` | The process SD, governing cross-process operations. |

These are the inspectable fields. Internal fields (refcounts, lock state) are not exposed.

## Inspecting your own process

For a thread inspecting its own process's PSB, the path is:

1. **Open the process's primary token** via `kacs_open_self_token` (with the `KACS_REAL_TOKEN` flag if you need the primary specifically, not the impersonation). The returned fd lets you query token state.
2. **Query through the process-related classes** — `TokenSessionId` and related — which return PSB-adjacent state where available.
3. **Read the process SD** via `kacs_get_sd` with a self-targeted query (using the appropriate flags for "this process").

For some PSB fields, dedicated query routes exist:

- The PIP fields can be read by querying the calling process's PSB through a dedicated path. The typical surface is via the token's session/process classes, which carry the PIP fields as part of the per-token snapshot.
- The mitigation bitfield is readable from the process itself; the typical pattern is to query the PSB directly via the appropriate ioctl.

The exact API for reading the PSB is in the [Kernel ABI reference](~peios/kernel-abi-reference/overview); the conceptual point for this page is that all PSB fields are introspectable by the process itself, with no privilege required.

## Inspecting another process's PSB

To inspect another process's PSB, you need:

- **`PROCESS_QUERY_INFORMATION`** on the target's process SD.
- **PIP dominance** over the target (the caller's PIP must dominate the target's, per the [two-check rule](~peios/process-integrity-protection/the-two-check-rule)).

Both requirements apply. A token-bearing principal granted `PROCESS_QUERY_INFORMATION` cannot inspect a higher-PIP process even with the SD grant — the PIP check is independent.

Once both checks pass, the same query mechanisms work: open the target's primary token (via `kacs_open_process_token`), query through `KACS_IOC_QUERY`, read the process SD via `kacs_get_sd`.

The PIP dominance requirement is the same one that gates every cross-process operation. A low-trust caller cannot see into a high-trust process even via inspection. A SeDebugPrivilege-holder can bypass the SD check (`PROCESS_QUERY_INFORMATION` becomes trivially granted) but **does not** bypass PIP — a privileged debugger still cannot inspect TCB processes.

In practice, only peinit and processes signed at the same PIP level as the target can inspect TCB processes. Ordinary administrators with `SeDebugPrivilege` are blocked at the PIP layer.

## Reading the process SD

A process's SD is read via `kacs_get_sd` with the appropriate process-targeted flags. The call:

```
kacs_get_sd(target_pidfd, SECURITY_INFORMATION_OWNER | DACL | ... etc, buf, buf_len, flags)
```

Returns the SD components requested (per the security_information mask). Self-targeted queries are always allowed; cross-process queries require `READ_CONTROL` on the target's process SD plus PIP dominance.

`READ_CONTROL` is one of the standard rights every SD-bearing object exposes; it appears in the DACL like any other right. By default the owner of an object has it implicitly (see [Ownership](~peios/security-descriptors/ownership)).

For inspecting the SACL specifically — to see audit ACEs, mandatory labels, PIP trust labels, scoped policy references — `ACCESS_SYSTEM_SECURITY` is the right needed, not `READ_CONTROL`. That right is gated by `SeSecurityPrivilege`. So:

- DACL: needs `READ_CONTROL` (typically held by the owner).
- SACL: needs `ACCESS_SYSTEM_SECURITY` (typically held only by administrators with `SeSecurityPrivilege`).
- Owner / primary group SIDs: need `READ_CONTROL`.

A non-privileged caller can read a process's DACL (if granted) but not its SACL. For administrative inspection of the full SD including SACL, `SeSecurityPrivilege` is the lever.

## Reading mitigation flags

The mitigation bitfield on the PSB is read via a dedicated query path. For your own process the read is trivial. For another process the same `PROCESS_QUERY_INFORMATION` + PIP dominance rules apply.

The bitfield is the same one the kernel uses internally:

| Flag | Bit | Meaning |
|---|---|---|
| WXP | 0x001 | Write-XOR-Execute enabled |
| TLP | 0x002 | Trusted Library Paths enabled |
| LSV | 0x004 | Library Signature Verification enabled |
| CFI (legacy) | 0x008 | CFIF + CFIB combined alias |
| UI_ACCESS | 0x010 | Reserved |
| NO_CHILD | 0x020 | Forbid fork/clone-new-process |
| CFIF | 0x040 | Forward CFI |
| CFIB | 0x080 | Backward CFI |
| PIE | 0x100 | PIE-only exec |
| SML | 0x200 | Speculation mitigation lock |

A process's mitigation flags tell you what hardening it has enabled. Comparing this against the process's binary lets you reason about which exploitation paths are closed — a TCB-signed binary running with WXP, LSV, TLP, CFIF, CFIB, and PIE is comprehensively hardened; one with only PIE has minimal hardening.

The flags are one-way — once set, they cannot be cleared. So the snapshot you read now is also the snapshot for the rest of the process's life (modulo new flags being added). Re-reading produces the same or stricter result.

## Cross-referencing process and token

A common diagnostic pattern: given a process, know which session it is in, which user it acts as, what its PIP is, and what mitigations are active.

The sequence:

1. **Open the process's primary token** via `/proc/<pid>/token` or `kacs_open_process_token`.
2. **Query `TokenUser`** for the user SID.
3. **Query `TokenStatistics`** for `auth_id`. Cross-reference with `/sys/kernel/security/kacs/sessions` for session details.
4. **Read the PSB** for PIP and mitigations.
5. **Read the process SD** for who can act on this process.

Each step requires the appropriate access. Many fail closed if the caller does not have authority over the target. For self-targeted queries everything succeeds.

For a debugger or monitoring tool, this is the standard "tell me everything about this process" workflow. The pieces are independent (each query is its own ioctl), but they combine to give a complete picture.

## Live vs static state

A process's state changes over time. The current state is what the inspection surfaces return; previous state is not retrievable.

The **changing** parts of a process's state:

- **Threads come and go.** A process's set of threads is dynamic. Re-running per-thread inspection picks up the current set.
- **The thread's effective token may change** (impersonation install/revert). Re-querying gets the current value.
- **The primary token's adjustable fields** (privileges enabled state, groups enabled state, default DACL) can change. The `modified_id` counter on the token tracks how many changes have happened.
- **The process SD can be modified** by anyone with `WRITE_DAC` on the process. New ACEs appear; old ACEs disappear.

The **immutable** parts of a process's state (once set):

- **PIP fields.** Set at exec; never change for the lifetime of the process.
- **Mitigation flags.** One-way; can be tightened but never relaxed.
- **`no_child_process` flag.** One-way.
- **Token identity fields** (user_sid, groups[].sid, restricted_sids, logon_sid). Set at token creation; the token can be replaced but never have its identity adjusted.

Knowing which fields are immutable helps with monitoring. A monitor that has already read the PIP fields once does not need to re-read them; they will not change. A monitor watching for privilege state changes needs to poll or subscribe to events — they can change at any time.

## What inspection cannot tell you

A few clarifications:

- **It cannot tell you what access a process has.** Inspection gives you the inputs to AccessCheck (the token, the object's SD); it does not compute the access. To know what a process can do to a specific object, call AccessCheck.
- **It cannot give you a tamper-evident snapshot.** The kernel may modify state between two reads; there is no "atomic snapshot" surface. Tools that need consistency should use the `modified_id` counter to detect changes.
- **It cannot reveal contents of memory inspection of the target process needs.** Inspecting the PSB and the process SD shows you the kernel's metadata about the process. To read the process's *memory* you need `PROCESS_VM_READ` on the process SD plus PIP dominance plus a ptrace-like syscall. That is a different topic.
- **It cannot show you removed history.** A token whose privileges were once enabled but have since been removed shows the current state, not the history. The `used` bit on a privilege is a sticky record of "this privilege has been exercised at some point", but specific timestamps are an audit-log concern, not an inspection concern.

The inspection surfaces are for the present moment. For historical questions, the audit log is the right source.
