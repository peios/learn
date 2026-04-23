---
title: Understanding Auditing on Peios
type: concept
description: How SACL-based audit rules record access decisions, including conditional, continuous, and privilege-use auditing.
---

Access control decides whether to grant or deny. **Auditing** records that the decision was made — who accessed what, when, and how.

Audit rules live in the same security descriptor as access rules, use the same SID matching, and are evaluated in the same AccessCheck call. This integration means audit and access control share a vocabulary: the same ACE that grants the Backup Operators read access can have a corresponding audit ACE that logs every time that access is exercised.

Auditing is purely observational. No audit rule affects the access decision — audit ACEs do not grant or deny rights. They are evaluated after the access decision is final, reading the result without modifying it.

## Access auditing

The primary auditing mechanism. **SYSTEM_AUDIT ACEs** in the SACL define which access attempts to log. Each audit ACE specifies:

| Field | What it controls |
|---|---|
| **SID** | Which principals are audited |
| **Access mask** | Which operations are audited (read, write, etc.) |
| **Success flag** | Whether to audit successful access |
| **Failure flag** | Whether to audit denied access |

An audit ACE with both success and failure flags audits every matching access attempt — successful and denied. An ACE with only the failure flag audits denied attempts, which is useful for detecting unauthorized access patterns without generating noise from legitimate access.

When an audit ACE's SID matches the caller, its mask overlaps with the access result, and its flags match the outcome, an **audit event** is emitted.

### Conditional audit ACEs

Audit ACEs can carry conditional expressions, just like DACL ACEs. A conditional audit ACE only fires when the expression evaluates to true:

```
Audit  Authenticated Users  FILE_WRITE_DATA  (success)
  IF (@Resource.classification == "confidential")
```

This audits successful writes to confidential files only. Writes to unclassified files are not logged.

One important difference from conditional DACL ACEs: when a conditional audit expression evaluates to UNKNOWN (a referenced claim or attribute is missing), the audit event **is emitted**. When in doubt, audit. Missing data should not silently suppress security logging.

## Continuous auditing

Access auditing fires once — at the point where the object is opened. It records "user X opened file Y with read access." It does not record what happens afterward: how many bytes were read, how many times, or whether specific operations occurred.

**Continuous auditing** fills this gap. Special ACEs in the SACL configure per-operation audit masks. When a file is opened and a continuous audit ACE matches, the kernel records an audit mask on the open handle. On each subsequent operation (read, write, execute), if the operation matches the handle's audit mask, an event is emitted.

This enables "audit every write to this file" rather than just "audit when this file is opened for write." Use cases include:

- **Compliance logging** for sensitive files — every access recorded
- **Exfiltration detection** — monitoring how often and how much data is read from classified objects

The cost is paid only on objects that carry continuous audit ACEs. Most objects have no continuous auditing, and the overhead is zero.

## Privilege-use auditing

When a privilege is exercised to grant access that the DACL would not have granted on its own, a **privilege-use audit event** is emitted. This records not just "access was granted" but "access was granted because SeBackupPrivilege was used."

This distinguishes policy-granted access from privilege-granted access in the audit trail. An administrator reviewing logs can see when privileges were used and whether that usage was expected.

Privilege-use auditing only fires when the privilege was actually necessary for the final result. If a later stage in the pipeline revoked the privilege-granted rights, no audit is emitted — the privilege did not contribute to the effective access.

## Per-token audit policy

Tokens can carry **audit policy overrides** that force auditing regardless of the object's SACL. This allows per-principal audit rules: "audit all access by this user" or "audit all access by members of the External Contractors group."

Per-token audit policy is set at token creation time. It augments the object's SACL — it does not replace it. If either the object's SACL or the token's audit policy calls for an event, the event is emitted.

## What an audit event contains

Each audit event captures:

| Field | Contents |
|---|---|
| **Subject** | The calling token's identity — user SID, group SIDs, integrity level |
| **Object** | What was accessed — file path, registry key, IPC endpoint |
| **Access** | What was requested, what was granted, whether it succeeded or failed |
| **Trigger** | Which audit ACE matched, or which privilege was exercised |
| **Process** | The calling process's PID, name, and executable path |

These events flow from the kernel through a ring buffer to the event daemon (eventd), which persists them for querying and analysis.
