---
title: Inspecting security state
type: how-to
description: Choose a supported read-only view of tokens, sessions, process protection or object policy, and understand what missing or refused information can establish.
related:
  - peios/access-decisions/debugging-a-denial
  - peios/inspecting/tokens
  - peios/inspecting/sessions
  - peios/inspecting/processes
  - peios/system-and-processes/token
  - peios/system-and-processes/logonse
  - peios/threads-and-processes/task-manager
  - peios/logs-and-events/event-viewer
---

Inspection answers a specific question about the running system: who a process
acts as, which session it belongs to, how it is protected, or what policy covers
an object. Start with the supported command or desktop view for that question,
and keep any access refusal or incomplete-view notice with the result.

For a failed operation, start with [Debugging a denial](~peios/access-decisions/debugging-a-denial).
It puts the caller, object and requested action together before interpreting
security state. A token dump alone does not tell you whether access is allowed.

## What you can inspect

These are read-only ways to begin. Replace `PID`, `TID` and `ID` with targets you
have identified, and the example paths with the actual objects.

| Question | Supported view | Interpretation limit |
|---|---|---|
| Which process is involved? | [Task Manager](~peios/threads-and-processes/task-manager), **Processes** | Some command, owner and protected-process details may be hidden. |
| Who does a process act as, and what is on its token? | [`token show --pid PID --all`](~peios/system-and-processes/token) | This selects the primary token; a thread may be impersonating. |
| What identity is a thread impersonating? | `token show --pid PID --tid TID --all` | Identify the failing thread and record the time; it may have reverted since the failure. |
| What is this process's protection? | [`logonse psb --pid PID`](~peios/system-and-processes/logonse#logonse-psb) | The PSB reports PIP, mitigations and process GUID, not its security descriptor. |
| Which logon sessions and processes are visible? | `logonse list`, `logonse show ID`, or Task Manager's **Signed in** | The session list and the visible-process list have different access limits. |
| What rules protect a file? | [`sd show ./report.txt --all`](~peios/files-and-directories/sd#sd-show) | Descriptor inspection is access-controlled; unreadable parts remain unknown. |
| What rules protect a registry key? | [`reg sd Machine/App`](~peios/registry-tools/reg#reg-sd-key) | The default view is owner, group and DACL; SACL reading needs separate authority. |
| What was recorded about an earlier attempt? | [Event Viewer](~peios/logs-and-events/event-viewer) or [evctl](~peios/evctl/using-evctl) | Audit policy, reader permissions, query scope, retention and transport all limit the answer. |

For files, `sd check` can explain a simulated access check without performing the
file operation. Read [the rehearsal's limits](~peios/access-decisions/debugging-a-denial#rehearse-a-file-check-within-its-limits)
before treating its result as an explanation of an application's failure.

## Who can inspect what

The tool does not add authority. The underlying surface determines which checks
apply:

- **Another process's token:** `PROCESS_QUERY_INFORMATION` on the process, PIP
  dominance, and `TOKEN_QUERY` on the token's own descriptor. Administrator
  membership does not bypass PIP or a changed token descriptor.
- **Another process's PSB:** `PROCESS_QUERY_LIMITED` on the process descriptor;
  PIP dominance is not required for this view. Seeing its protection does not
  grant access to its token or memory.
- **Another process's descriptor:** `READ_CONTROL` plus PIP dominance for owner,
  group and DACL inspection. SACL inspection additionally needs
  `ACCESS_SYSTEM_SECURITY`. See [Inspecting processes](~peios/inspecting/processes).
- **The kernel's full session listing:** Administrators or SYSTEM, through the
  descriptor on `/sys/kernel/security/kacs/sessions`. `logonse` reports a refusal
  and can fall back to the sessions of processes you may inspect. Even an
  administrator's process list can omit protected processes.

Self-access is surface-specific. The Kernel TRM documents a process opening its
own `/proc` token paths without the cross-process or token-descriptor checks.
Opening its own token through the API still checks the token descriptor; a
changed descriptor can revoke that access. Do not turn the first rule into a
promise that every self-query succeeds. See
[Token access rights](~peios/peios-kernel/kacs/tokens/access-rights).

A refused inspection is a result in its own right. Keep the target, operation
and error; ask an authorised operator or the component owner for the missing
evidence when needed. Do not change permissions, disable protection or adjust a
token just to obtain a fuller report.

## What you cannot inspect

These views have boundaries even when they return successfully:

- **No complete history.** They report current state. A destroyed token cannot
  be recovered from a live query, and an earlier impersonation or privilege
  state may have changed. Use recorded evidence for historical questions.
- **No atomic machine snapshot.** Processes and threads start and exit during a
  listing. Separate token queries can observe adjustments between reads; keep
  the token ID and modification counter where available.
- **No global inventory of every token.** Process-based inspection cannot list
  tokens held only by file descriptors with no running process using them.
- **No implied access verdict.** A token, PSB or descriptor report supplies
  inputs, not the outcome of every possible operation.
- **No inferred absence from a partial view.** Hidden processes, unreadable
  descriptor components and missing audit records remain unknown. A source or
  syscall error is not a successful empty result.

For registry output, use the documented result distinctions: `reg` exit `2`
means a key/value was not found, `3` is access denied, and `5` is another syscall
or source error. An empty value or listing alone is not one of those diagnoses.
See [`reg` exit status](~peios/registry-tools/reg#exit-status).

## Standard query patterns

**Follow a process to its session.** Find the process in Task Manager, inspect
its primary token, and use the reported logon-session ID with `logonse show ID`.
`token show` labels this `session_id`; in the underlying statistics it is
`auth_id`. It is distinct from `interactivity_scope`. A service's impersonated
request may belong to a different session, so retain which token you inspected.

**Explain why a protected process has limited details.** Read its Protection
field in Task Manager or its PSB with `logonse psb --pid PID`. A visible PSB and
a refused token query can both be correct under the separate access rules.

**Investigate a privilege-related refusal.** Use `token privs --pid PID` for the
primary token, or the documented thread selector when impersonation is involved.
Separate present from enabled; neither proves the application supplied any
required intent or that another policy allowed the operation. Continue with
[Debugging a denial](~peios/access-decisions/debugging-a-denial#privileges).

## Two ways to read a token

For an operator, [`token`](~peios/system-and-processes/token) opens and queries
the token, then renders readable output. [Inspecting tokens](~peios/inspecting/tokens)
explains how to select the target and interpret the fields.

For a tool author, token file descriptors and `KACS_IOC_QUERY` expose structured
state. `/proc/<pid>/token` selects the process's primary token;
`/proc/<pid>/task/<tid>/token` selects the thread's effective token. These and
`/sys/kernel/security/kacs/self` provide handles, not text to print with `cat`.
The SDK [token-opening](~peios/sdk-tokens/opening-and-creating-tokens) and
[query](~peios/sdk-tokens/query) references document the programming interface;
the Kernel TRM [ABI notes](~peios/peios-kernel/kacs/kacs-abi-notes#querying-a-token-handle)
cover the raw query protocol.

Other pseudo-files have different formats: the documented session listing and
`/proc/<pid>/psb` are text. The existence of one text surface does not make token
handles text, or make every surface follow the same access rules.

## Where to start

- [Inspecting tokens](~peios/inspecting/tokens): choose a token and interpret its
  identity, groups, privileges and restrictions.
- [logonse](~peios/system-and-processes/logonse) and
  [Inspecting sessions](~peios/inspecting/sessions): session reports, their
  coverage, and the underlying listing format.
- [Task Manager](~peios/threads-and-processes/task-manager) and
  [Inspecting processes](~peios/inspecting/processes): process views and the
  separate token, PSB and descriptor surfaces.
- [Debugging a denial](~peios/access-decisions/debugging-a-denial): combine these
  observations with the failed action and object policy.
- [The event stream](~peios/inspecting/the-event-stream): raw transport diagnosis
  when events are not reaching eventd. For ordinary recorded-event inspection,
  use Event Viewer or evctl instead.
