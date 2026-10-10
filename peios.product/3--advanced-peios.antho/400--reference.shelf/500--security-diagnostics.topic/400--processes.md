---
title: Inspecting processes
type: concept
description: Inspecting a process's PSB (PIP, mitigations) through /proc/<pid>/psb, and its process SD. Your own state is free; another process's PSB needs PROCESS_QUERY_LIMITED, and its SD needs READ_CONTROL plus PIP dominance.
related:
  - peios/threads-and-processes/task-manager
  - peios/system-and-processes/logonse
  - peios/inspecting/debugging-a-denial
  - peios/inspecting/overview
  - peios/inspecting/tokens
  - peios/security-diagnostics/sessions
  - peios/process-integrity-protection/overview
  - peios/process-integrity-protection/the-process-security-descriptor
  - peios/process-mitigations/overview
---

A process's inspectable state spans three things: its **token** (its identity), its **PSB** (its PIP labels and mitigation flags), and its **process SD** (the policy on the process as an object). Each is read through its own surface. Your own state is always readable; another process's needs a right on its process SD, and for everything but the PSB, PIP dominance too.

This page covers the per-process inspection surfaces beyond the token. Tokens are covered in [Inspecting tokens](~peios/inspecting/tokens); this page is about the PSB and the process SD.

## What the PSB holds

The Process Security Block is the per-process kernel structure with:

| Field | Meaning |
|---|---|
| `pip_type` | The process's PIP type: 0 for none, 512 for Protected. |
| `pip_trust` | The PIP trust level within the type: 8192 for `PeiosTcb`. |
| Mitigation flags | The bitfield of enabled mitigations (WXP, LSV, TLP, CFIF, CFIB, PIE, SML, NO_CHILD, etc.). |
| `process_guid` | The process's identity for its whole life, unlike its PID, which is reused. Events carry it. |

The process SD sits beside the PSB and is read separately (below). Internal fields (refcounts, lock state) are not exposed.

## Reading a PSB

`/proc/<pid>/psb` is one line of text:

```
pip_type=512 pip_trust=8192 mitigations=0x105 process_guid=3f2c9a1e-6b0d-4c8e-9a41-2d7e5f10b6c3
```

`mitigations` is the bitfield below, in hexadecimal.

- **Your own** is always readable.
- **Another process's** needs `PROCESS_QUERY_LIMITED` on its process SD — the right `ps` needs for a process's name and CPU use, which the default process SD gives Everyone.

PIP dominance is **not** required here, and this is the only inspection surface where it is not. That a process is protected, and at what trust, is not a secret the kernel keeps: every other refusal already reveals it. Reading it is what lets a tool such as Task Manager say *why* the rest of a process is closed — "protected: signed Peios TCB" rather than an unexplained "access denied".

## Inspecting another process

Everything beyond the PSB needs two things:

- **The right on the target's process SD**: `PROCESS_QUERY_INFORMATION` for its token and detailed `/proc` entries, `READ_CONTROL` for its process SD.
- **PIP dominance** over the target (the caller's PIP must dominate the target's, per the [two-check rule](~peios/process-integrity-protection/the-two-check-rule)).

Both requirements apply. A principal granted `PROCESS_QUERY_INFORMATION` cannot inspect a higher-PIP process even with the SD grant — the PIP check is independent.

Once both checks pass, open the target's primary token (via `/proc/<pid>/token` or `kacs_open_process_token`), query through `KACS_IOC_QUERY`, and read the process SD via `kacs_get_sd`. Reading the token needs `TOKEN_QUERY` on the token's own descriptor as well, which by default its user, its creator, SYSTEM and Administrators have.

A SeDebugPrivilege-holder can bypass the process SD check (`PROCESS_QUERY_INFORMATION` becomes trivially granted) but does not bypass PIP — a privileged debugger still cannot inspect TCB processes.

In practice, only peinit and processes signed at the same PIP level as the target can inspect TCB processes. Ordinary administrators with `SeDebugPrivilege` are blocked at the PIP layer, and see such a process's PSB and nothing else.

## Reading the process SD

A process's SD is read via `kacs_get_sd` with the appropriate process-targeted flags. The call:

```
kacs_get_sd(target_pidfd, security_information, buf, buf_len, flags)
```

Returns the SD components requested (per the security_information mask). Self-targeted queries are always allowed; cross-process queries require `READ_CONTROL` on the target's process SD plus PIP dominance.

`READ_CONTROL` is one of the standard rights every SD-bearing object exposes; it appears in the DACL like any other right. By default the owner of an object has it implicitly (see [Ownership](~peios/security-descriptors/ownership)).

For inspecting the SACL specifically — to see audit ACEs, mandatory labels, PIP trust labels, scoped policy references — `ACCESS_SYSTEM_SECURITY` is the right needed, not `READ_CONTROL`. That right is gated by `SeSecurityPrivilege`. So:

- DACL: needs `READ_CONTROL` (typically held by the owner).
- SACL: needs `ACCESS_SYSTEM_SECURITY` (typically held only by administrators with `SeSecurityPrivilege`).
- Owner / primary group SIDs: need `READ_CONTROL`.

A non-privileged caller can read a process's DACL (if granted) but not its SACL. For administrative inspection of the full SD including SACL, `SeSecurityPrivilege` is the lever.

## Reading mitigation flags

The mitigation bitfield is the `mitigations` value in `/proc/<pid>/psb`, under the rule in [Reading a PSB](#reading-a-psb). It is the same one the kernel uses internally:

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

The flags are one-way — once set, they cannot be cleared. So the snapshot you read now is also the snapshot for the rest of the process's life (except that new flags may be set). Re-reading produces the same or stricter result.

## Cross-referencing process and token

A common diagnostic pattern: given a process, know which session it is in, which user it acts as, what its PIP is, and what mitigations are active.

The sequence:

1. **Open the process's primary token** via `/proc/<pid>/token` or `kacs_open_process_token`.
2. **Query `TokenUser`** for the user SID.
3. **Query `TokenStatistics`** for `auth_id`. Cross-reference with `/sys/kernel/security/kacs/sessions` for session details.
4. **Read `/proc/<pid>/psb`** for PIP and mitigations.
5. **Read the process SD** for who can act on this process.

Each step requires the appropriate access, and each fails closed if the caller lacks authority over the target. For self-targeted queries everything succeeds.

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
- **Mitigation flags** (including `NO_CHILD`). One-way; can be tightened but never relaxed.
- **Token identity fields** (user_sid, groups[].sid, restricted_sids, logon_sid). Set at token creation; the token can be replaced but never have its identity adjusted.

Knowing which fields are immutable helps with monitoring. A monitor that has already read the PIP fields once does not need to re-read them; they will not change. A monitor watching for privilege state changes needs to poll or subscribe to events — they can change at any time.

## What inspection cannot tell you

A few clarifications:

- **It cannot tell you what access a process has.** Inspection gives you the inputs to AccessCheck (the token, the object's SD); it does not compute the access. To know what a process can do to a specific object, call AccessCheck.
- **It cannot give you a tamper-evident snapshot.** The kernel may modify state between two reads; there is no "atomic snapshot" surface. Tools that need consistency should use the `modified_id` counter to detect changes.
- **It cannot reveal the contents of the target process's memory.** Inspecting the PSB and the process SD shows you the kernel's metadata about the process. To read the process's *memory* you need `PROCESS_VM_READ` on the process SD plus PIP dominance plus a ptrace-like syscall. That is a different topic.
- **It cannot show you removed history.** A token whose privileges were once enabled but have since been removed shows the current state, not the history. The `used` bit on a privilege is a sticky record of "this privilege has been exercised at some point", but specific timestamps are an audit-log concern, not an inspection concern.

The inspection surfaces are for the present moment. For historical questions, the audit log is the right source.

## Where to go next

For inspecting the live flow of audit events rather than current state, read [The event stream](~peios/security-diagnostics/the-event-stream).

For the identity half of a process's state — obtaining and querying token fds — read [Inspecting tokens](~peios/inspecting/tokens).

For the dominance rule that gates every cross-process inspection, read [The two-check rule](~peios/process-integrity-protection/the-two-check-rule).
