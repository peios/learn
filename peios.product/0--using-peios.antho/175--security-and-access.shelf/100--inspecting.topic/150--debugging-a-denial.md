---
title: Debugging a denial
type: how-to
description: Diagnose an access refusal with the caller, object and operation in hand, using supported inspection tools, audit evidence and policy-specific next steps.
related:
  - peios/access-decisions/overview
  - peios/threads-and-processes/task-manager
  - peios/system-and-processes/token
  - peios/files-and-directories/sd
  - peios/registry-tools/reg
  - peios/logs-and-events/event-viewer
  - peios/inspecting/overview
  - peios/sdk-access-control/checking-access
---

Start with the operation that failed, then gather the evidence you are allowed
to read. The aim is to explain the refusal and decide whether the caller or the
policy needs review. A refusal can be the intended protection working.

Use the inspection commands below before changing permissions, privileges or
labels. An empty registry result or a missing process detail is not, by itself,
evidence that a particular access-check layer denied the original operation.

## Record the failed operation

Keep these together:

- **What failed and when:** the application's message, error or exit status,
  timestamp, and the action you asked it to perform.
- **The caller:** the application or service, its PID, and the failing thread's
  TID if the application's diagnostics identify it. A service acting for a
  client may be using an impersonation token rather than its primary token.
- **The object:** the exact file path, registry key, process or other resource.
  For a file, establish whether the operation targeted a symbolic link or its
  target. For a registry operation, keep the key and value name separate.
- **The access requested:** read, write, execute, change permissions, or another
  specific operation. Keep the requested access mask when the diagnostic or
  audit record supplies it; an application may ask for more than its visible
  action suggests.
- **The point of failure:** opening an object, using an already-open handle,
  or a service's own authorisation check. These are different questions.

Access is normally decided when a handle is opened. Later operations use the
rights stored on that handle; inspecting today's descriptor does not reconstruct
what an older handle received. See [The decision is made at open](~peios/access-decisions/overview#the-decision-is-made-at-open-and-it-stays-made).

## Find the thread and its tokens

Use [Task Manager](~peios/threads-and-processes/task-manager) to find the process
by name, PID, person or service. Check its command, owner, service or job, and
signed-in session where visible. Read any notice about hidden details or
protection before interpreting the view.

In a terminal, use the read-only subcommands of
[`token`](~peios/system-and-processes/token). Replace `PID` and `TID` with the
identified process and thread:

```console
token show --pid PID --all
token privs --pid PID
token show --pid PID --tid TID --all
```

`--pid` selects the process's **primary** token. The command's `--tid` selector
is for a thread's impersonation token and is used with `--pid`; use it when
investigating impersonation. The identity that matters is the one the failing
thread used: its impersonation token while impersonating, otherwise its primary
token. If that identity is no longer available, record the gap rather than
substituting the inspection tool's own token. Running `token show --all` without
a target shows the tool's own token, not another application's.

The `/proc/<pid>/token`, `/proc/<pid>/task/<tid>/token` and
`/sys/kernel/security/kacs/self` surfaces provide token **handles**, not text to
read with `cat`. The process path identifies the primary token; the thread path
identifies the effective token. The command does the querying and decoding.
[Inspecting tokens](~peios/inspecting/tokens) documents those interfaces for tool
authors.

Record the user SID, group attributes, token type and impersonation level,
integrity and mandatory policy, present and enabled privileges, restricted SIDs,
and confinement identity and capabilities where available. Keep token and
session IDs with the time of inspection: the thread can revert impersonation,
and token adjustments can change the state after the failure.

For process protection and session context, use
[`logonse`](~peios/system-and-processes/logonse):

```console
logonse psb --pid PID
logonse list
logonse show ID
```

Here `ID` is the logon-session ID you have identified. `token show` calls it
`session_id`; it is separate from `interactivity_scope`. A PSB report shows
protection, mitigations and the process GUID; it is not the process's security
descriptor.

**Inspection has its own access checks.** Reading another process's token needs
`PROCESS_QUERY_INFORMATION`, PIP dominance, and `TOKEN_QUERY` on the token.
Reading its PSB needs `PROCESS_QUERY_LIMITED` and does not require PIP dominance.
The full kernel session list is restricted to Administrators and SYSTEM;
`logonse` can show a partial process-based view instead. A refused query or an
absent process in that view is a limit on your evidence, not a reason to remove
protection. See [Who can inspect what](~peios/inspecting/overview#who-can-inspect-what).

## Find the object and its SD

For a file, [`sd show`](~peios/files-and-directories/sd#sd-show) queries owner,
group, DACL and the integrity-label subset:

```console
sd show ./report.txt --all
```

Replace the example path with the object you identified. `sd` follows a named
symbolic link by default; its documented `--no-follow-symlinks` option selects
the link itself. Inspect the same object the failed operation meant to reach.
`--all` changes formatting, not selection: this view does not include audit
ACEs or the rest of the SACL, and its summaries omit some ACE payload details.
Do not infer that undisplayed policy is absent.

For a registry key, [`reg sd`](~peios/registry-tools/reg#reg-sd-key) prints owner,
group and DACL by default:

```console
reg sd Machine/App
```

Only when you already have the authority to read the SACL, request it explicitly:

```console
reg sd Machine/App --sacl
```

The full SACL needs `ACCESS_SYSTEM_SECURITY`; the default registry
owner/group/DACL view does not establish which SACL labels or policies exist. Similarly, a refused
`sd show` is a failed inspection, not a decoded explanation of the original
operation. Keep the returned error and the scope of any descriptor you obtained.
For a process's descriptor, use the separate
[process-SD inspection reference](~peios/security-diagnostics/processes#reading-the-process-sd)
with an authorised diagnostic tool; the PSB and a token report do not replace it.

In the parts you can read, look for:

- **Owner and DACL:** the owner SID, ordered allow/deny ACEs, inheritance flags,
  and the SIDs and rights each ACE names. `INHERIT_ONLY` (`IO`) rules apply to
  descendants rather than this object. A non-inherit-only access-control ACE
  naming `OWNER RIGHTS` suppresses the owner's implicit `READ_CONTROL | WRITE_DAC`
  grant.
- **Mandatory label:** the first applicable `SYSTEM_MANDATORY_LABEL_ACE` in the
  SACL and its policy bits.
- **Process-trust label:** an applicable `SYSTEM_PROCESS_TRUST_LABEL_ACE` and
  the rights its mask allows a non-dominant caller.
- **Other policy inputs:** scoped central-policy references
  (`SYSTEM_SCOPED_POLICY_ID_ACE`), resource attributes
  (`SYSTEM_RESOURCE_ATTRIBUTE_ACE`) and conditional ACEs.

A component omitted from your permitted view is unknown, not empty. Reading an
owner or finding one allow ACE is not enough to establish effective access.

## Rehearse a file check, within its limits

For a file, [`sd check`](~peios/files-and-directories/sd#sd-check) explains a
check without performing the requested file operation:

```console
sd check ./report.txt read --pid PID --explain
```

Choose the documented permission name or mask that matches the failed request.
Without `--pid`, the check uses your own token. Save the explanation and any
error, not just the exit status: a non-zero status can also mean the path was
unreachable or the tool could not complete the check.

Treat this as evidence about the inputs tested. The command documents a process
token selector, not a thread selector or switches for every optional
access-check input. It does not establish that it reproduced a service's
impersonated caller, local claims, backup/restore intent or process-trust context.
It also does not test rights on an existing handle. An allowed rehearsal is not
a guarantee that the application's full operation will succeed. If the result
differs, compare the caller, target, requested rights and timing before changing
policy.

## Check audit evidence

Check the recorded attempt alongside the live state, rather than treating logs
as a last resort. In [Event Viewer](~peios/logs-and-events/event-viewer), select
the relevant time range and filter **Type** to `kacs.audit.access.checked`.
Select a record to inspect its fields. The terminal route is
[Using evctl](~peios/evctl/using-evctl).

Correlate the timestamp, emitting process, subject token/session and object
information actually present in the record. The subject is the caller; an
`object.process.*` or `object.token.*` field identifies the target. Some checks
cannot supply a path or a complete object identity, so do not infer one.

For a matching [access-check record](~peios/events/kacs/kacs-audit-access-checked):

- Compare `access.requested` and `access.granted`. The requested mask is already
  generic-mapped to the object's rights.
- `access.denied-integrity` and `access.denied-trust`, when present, identify
  bits withheld by the mandatory-integrity or process-trust checks.
- `trigger.ace` identifies the **audit** ACE that caused a SACL-driven record;
  it is not a trace naming the DACL ACE that denied access.
- `fields.attestation.userspace` marks an advisory syscall check whose descriptor
  and supplied context came from userspace. It is not proof that the real
  operation used those same inputs.

For a [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used)
record with `operation.name` equal to `access-check`, a false `outcome.success`
means a privilege contributed rights that did not survive. It does not mean the
privilege was absent, and it does not identify one narrowing layer on its own.

**No record is not proof of no attempt.** Access auditing depends on matching
SACL rules or token policy, and syscall SACL records additionally require the
calling process's enabled `SeAuditPrivilege`. Reader permissions, query scope,
retention and transport loss also limit what you can see. One check can produce
several records; `MAXIMUM_ALLOWED` success is not evidence that a particular
right was granted, and it produces no access-check privilege-use record.
See [Find missing records](~peios/logs-and-events/find-missing-records).

Use [the raw event stream](~peios/security-diagnostics/the-event-stream) only to diagnose
the transport itself. It requires `SeSecurityPrivilege`, can lose events, and
is not a replacement for recorded history.

## The six places a denial can come from

For a completed access check, these are the common policy questions. They are
not a classification of every application error or failed inspection:

1. Could the impersonation token be used for access at all?
2. Did mandatory integrity control (MIC) withhold the requested rights?
3. Did process integrity protection (PIP) withhold them?
4. Did the DACL grant them for this caller?
5. Did a restricted-token pass, confinement or central policy narrow the grant?
6. Did an operation that legitimately needs a privilege have it present, enabled
   and, where required, accompanied by the caller's intent?

## Review the relevant policy

Use the evidence above to choose the relevant review below. The
[access-decision overview](~peios/access-decisions/overview) explains the complete
ordering; a visible allow rule or a hand-worked DACL alone is not a full verdict.

### Impersonation level

An **impersonation-type** token at Identification level cannot be used for an
access check. Confirm the type as well as the level. Ask the application's
owner to review what the client requested and whether the
[two-gate model](~peios/impersonation/the-two-gates) downgraded it. Identification
may have been deliberate; do not assume the client intended to delegate more
authority.

### MIC

Compare the caller's integrity and mandatory policy with the object's applicable
mandatory label and the requested rights. `NO_READ_UP`, `NO_WRITE_UP` and
`NO_EXECUTE_UP` affect the corresponding mapped categories. An object without an
applicable label defaults to Medium with no-write-up; an unreadable SACL does
not establish that this default applies.

Review whether the workload was launched at its intended integrity and whether
the object's label matches its purpose. Do not lower a label or elevate the
caller merely to make the test pass. MIC does not revoke rights already granted
by backup/restore privileges, so an integrity mismatch alone is not the full
answer. See [Mandatory integrity control](~peios/access-decisions/mandatory-integrity-control).

### PIP

PIP compares process trust, not the user's identity or token integrity. Both
caller trust axes must dominate the object's applicable trust label; otherwise
the label's mask limits the allowed rights and can revoke privilege grants.
Use the permitted PSB view and any recorded `access.denied-trust` evidence.

For a protected service, review whether the client is using its supported
interface and intended binary. Administrator membership or another privilege
does not bypass this boundary. Review unexpected protection or signing state
with the component owner. See [Process integrity protection](~peios/process-integrity-protection/overview).

### Privileges

First establish that this operation is intended to use a privilege. Then
separate three findings:

- **Absent:** review the principal's privilege assignment with its policy owner.
- **Present but disabled:** review the application's use of that privilege.
- **Enabled but intent missing:** backup/restore intent belongs to the caller's
  operation, and cannot be inferred from the token dump.

A privilege's presence is not a general access grant. Enabling privileges or
adding backup/restore intent is not a routine repair for an ordinary read or
write. PIP, confinement and central policy can still constrain privilege-granted
rights. See [Privileges in the pipeline](~peios/access-decisions/privileges-in-the-pipeline)
and [Intent-gated privileges](~peios/privileges/intent-gated).

### The DACL walk

Compare the requested rights with the ordered ACEs and the caller's actual SID
set. Enabled groups participate in allows; deny-only groups participate in
denies. Check `INHERIT_ONLY`, owner-rights suppression and inherited rules before
concluding that a rule applies. For conditional ACEs, missing claims or resource
attributes can produce UNKNOWN, which does not grant access through an allow
ACE.

ACE order matters: the walk is first-writer-wins for each undecided right, not a
search for any matching allow. Use [DACL evaluation](~peios/security-descriptors/dacl-evaluation)
and [Ownership](~peios/security-descriptors/ownership) for the exact matching
rules, including `OWNER RIGHTS` and `PRINCIPAL_SELF`.

If the evidence points to the DACL, ask the resource's policy owner to compare
its intended audience and rights with the current rules and inheritance. Avoid
broad grants, ownership changes or inheritance resets as diagnostic shortcuts.

### Narrowing layers

A DACL grant may still be narrowed:

- **Restricted token:** compare the restricting SIDs with the object's rules.
  The write-restricted variant narrows only write-category rights. Privilege
  grants can survive this pass; review the application's token construction.
- **Confinement:** compare the confinement SID and declared capabilities with
  the resource policy. Privileges do not bypass confinement. Review the
  workload's intended capabilities with its deployment or policy owner.
- **Central access policy (CAAP):** check referenced effective policies, their
  applicability and resource attributes with the directory/policy owner. A
  missing policy uses the documented recovery policy. A staged-policy mismatch
  is a rollout signal, not a statement that the staged policy caused the denial.

Do not remove restrictions, confinement or central-policy references to test a
hypothesis. See [Narrowing layers](~peios/access-decisions/narrowing-layers) for
the separate mechanisms and their policy-specific references.

## A compact checklist

1. Keep the failing action, time, caller, object, requested rights and exact
   error together.
2. Identify the process in Task Manager; inspect the relevant token and PSB
   using the documented commands and your existing authority.
3. Read the descriptor components you are allowed to see. Mark inaccessible
   components as unknown.
4. For a file, use `sd check --explain` with the identified target and rights;
   record which inputs the rehearsal does and does not reproduce.
5. Correlate available audit evidence. Account for missing records and changes
   since the failure.
6. Take the finding to the appropriate application or policy owner. After an
   approved correction, verify the original operation in its intended context;
   a changed descriptor or an allowed rehearsal alone is not completion.

## When the evidence is incomplete

Hand the investigation to the application or resource-manager developer when
the failure depends on a transient impersonation token, caller-supplied claims,
intent flags, object-type mapping or other inputs the operator tools cannot
reproduce. Include the evidence collected, its timestamps and scope, and each
inspection that was refused. Do not fill missing inputs with guesses.

The existing [SDK checking-access guide](~peios/sdk-access-control/checking-access)
covers programmatic evaluation. Its [request reference](~peios/sdk-access/the-request)
defines the token, descriptor, desired mask, generic mapping, privilege intent,
self SID, local claims, object tree, PIP context and audit context. The
[check](~peios/sdk-access/the-check) and [audit outputs](~peios/sdk-access/audit-outputs)
references describe the granted mask, continuous-audit mask and staging-mismatch
flag. The Kernel TRM [KACS ABI](~peios/peios-kernel/kacs/kacs-abi) preserves the
raw syscall structures.

These checks are advisory. A developer must match the original inputs and
understand the [syscall's audit limits](~peios/peios-kernel/kacs/access-check/auditing)
before treating a reproduction as an explanation. Calling or decoding a syscall
is not a required operator step, and its answer does not perform or authorise
the original operation.

## Where to go next

- [Task Manager](~peios/threads-and-processes/task-manager) and
  [token](~peios/system-and-processes/token) for identifying the caller.
- [sd](~peios/files-and-directories/sd) and
  [registry access control](~peios/registry-security/access-control) for the
  object's policy and the supported inspection commands.
- [Event Viewer](~peios/logs-and-events/event-viewer) and
  [Find missing records](~peios/logs-and-events/find-missing-records) for recorded
  evidence and the limits of a search.
- [Inspecting security state](~peios/inspecting/overview) for the underlying
  interfaces and access requirements.
