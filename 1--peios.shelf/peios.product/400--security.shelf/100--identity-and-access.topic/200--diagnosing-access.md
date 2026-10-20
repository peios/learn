---
title: Diagnosing an Access Refusal
type: how-to
description: Combine the failing operation, effective caller, object policy, and recorded evidence before proposing a correction.
---

A refusal can be the intended policy working. Start with evidence from the
failed operation; a token dump or an isolated allow ACE cannot explain every
possible access decision.

## Gather the actual request

1. Record the operation, time, message, and exact error or exit status.
   Identify the process, failing thread, and managing service where known.
2. Identify the object and requested rights. Keep a registry key separate
   from its value name. Distinguish a link from its target and an open from
   an operation using an already-open handle.
3. Inspect the relevant effective token with existing authority. Preserve
   target selectors and the observation time: impersonation can have ended
   before inspection. Without a target, a tool usually observes itself.
4. Read the descriptor components available to that caller. Mark unreadable
   or undisplayed components as unknown, not empty.
5. Correlate recorded evidence and its collection limits. After a reviewed
   correction, repeat the original operation in its intended context.

An application can request more rights than its visible action suggests.
Capture the exact mask when diagnostics provide it. Rights on an existing
handle reflect the earlier open; today's descriptor does not reconstruct
that earlier decision.

## Choose a supported view

| Question | Read-only starting point | Limit |
|---|---|---|
| Process identity | `token show --pid PID --all` | Primary token, not necessarily the failing thread's effective token. |
| Impersonating thread | `token show --pid PID --tid TID --all` | Consecutive live queries cannot reconstruct an earlier token. |
| Present/enabled privileges | `token privs --pid PID` | Presence does not prove enablement, intent, or successful use. |
| Program protection | `logonse psb --pid PID` | PSB summary, not the process's security descriptor. |
| Session context | `logonse list` and `logonse show ID` | Can fall back to an incomplete visible-process view. |
| File descriptor policy | `sd show PATH --all` | Owner, group, DACL, and label subset; not a complete SACL export. |
| Registry descriptor | `reg sd KEY`, with `--sacl` when authorized | Default output omits SACL policy. |
| Recorded attempt | Event Viewer or `evctl` | Reader rights, collection, query scope, retention, and transport can limit evidence. |

For files, `sd` follows a named symlink unless its documented no-follow
option is selected. Inspect the same object the application meant to use.
Token pseudo-files provide handles, not text to print with `cat`.
[Token inspection](~peios/system-and-processes/token) and
[process-security inspection](~peios/system-and-processes/inspecting-process-security)
explain their separate access gates.

## Rehearse within the tool's limits

For an identified file and process, a read rehearsal is:

```sh
sd check ./report.txt read --pid PID --explain
```

Adapt the file, rights, and PID to the failed request. This does not perform
the file operation. A tool failure is different from a completed denied
check. The process selector does not reproduce every thread impersonation,
local claim, backup/restore intent, object mapping, or PIP context.
It also does not test an existing handle's rights.

An allowed rehearsal is therefore not proof that the application must
succeed. If the results differ, compare inputs and timing before changing
policy. A developer can use the [SDK request
reference](~peios/sdk-access/the-request) for inputs the operator tool cannot
supply, and its [checking guide](~peios/sdk-access-control/checking-access)
for the advisory result's limits.

## Review the relevant policy

| Evidence | Review |
|---|---|
| Identification-level impersonation token | Whether the client conveyed authority and the server was admitted to use it. |
| Mandatory-integrity refusal | Token integrity/mandatory policy, the applicable object label, and requested mapped rights. |
| Process-trust refusal | Calling PSB, target trust label, and intended signed interface; impersonation does not raise PIP. |
| Missing privilege contribution | Present versus enabled state and required operation intent. |
| DACL refusal | Ordered ACEs, enabled/deny-only SIDs, conditions, inheritance-only flags, and owner-rights suppression. |
| Restricted-token narrowing | The independent restricting SID view and any retained privilege grants. |
| Confinement narrowing | The intended confinement identity/capabilities and resource policy. |
| Central-policy narrowing | Effective policy, applicability, resource attributes, and recovery behavior; staged mismatches are separate evidence. |

MIC, PIP, privilege contributions, and narrowing occur in a defined pipeline.
Do not assume one label mismatch or one matching ACE explains the whole mask.
The [kernel access-check reference](~kernel/internals/kacs/access-check/overview)
is authoritative for ordering. Object-manager and service checks can also
reject an operation outside that pipeline.

## Interpret recorded evidence

`kacs.audit.access.checked` can record the subject, object, requested and
granted masks, and reasons. Auditing depends on policy; userspace checks
also have audit-authority requirements. One check can produce several records.
A successful `MAXIMUM_ALLOWED` result does not prove a particular bit was
granted. Inspect the returned mask.

Use [Finding Missing Records](~peios/reading-records/finding-missing-records)
before interpreting an empty search. Raw KMES inspection is a transport probe,
not historical proof. Preserve refused inspections, missing inputs, and
changed-state uncertainty in the report to the application or policy owner.
A narrower intended grant or corrected caller behavior should follow that
review; broad permission changes are not a diagnostic substitute.
