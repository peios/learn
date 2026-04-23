---
title: Troubleshooting Access Denied Errors
type: how-to
description: Diagnosing access denied errors by walking each AccessCheck pipeline layer from PIP through CAP.
---

When an operation fails with access denied, the denial could come from any layer in the AccessCheck pipeline. The fastest way to diagnose it is `sd explain` — but understanding the layers helps you interpret the result and know where to fix the problem.

## Start with sd explain

```bash
$ sd explain /srv/data/reports 1482 FILE_WRITE_DATA
```

The output walks through every layer and shows exactly where the denial occurred. Start here before investigating manually.

## The layers, in evaluation order

AccessCheck evaluates these layers in sequence. A denial at any layer stops evaluation — later layers are never reached.

### 1. PIP trust label

**Symptom:** Access denied even though the DACL clearly grants it, and the user has appropriate privileges.

**Check:** Does the object have a trust label in its SACL?

```bash
$ sd show /srv/data/reports
...
SACL:
  Trust Label: Protected / Trust 2048  (restrict: write)
```

**Fix:** PIP cannot be bypassed. The calling process must run a binary signed at the required trust level. If the access is legitimate, it must come from an appropriately signed process.

### 2. Integrity check (MIC)

**Symptom:** A process cannot write to an object, even though the DACL grants write access to the process's identity.

**Check:** Compare the process's integrity level against the object's mandatory label:

```bash
$ idn show 1482
...
Integrity:    Medium

$ sd show /srv/data/reports
...
SACL:
  Mandatory Label: High
```

Medium < High — write access is denied before the DACL is consulted.

**Fix:** Either lower the object's integrity label (requires `SeRelabelPrivilege`) or run the process at a higher integrity level (elevation).

### 3. DACL

**Symptom:** The most common cause. The process's identity does not match any allow ACE, or a deny ACE blocks the access.

**Check:** Look at which ACEs match (or don't):

```bash
$ sd explain /srv/data/reports 1482 FILE_WRITE_DATA
...
[3] DACL walk
    ACE 1: Deny  contractors  FILE_WRITE_DATA
           SID match: yes (token group)
           FILE_WRITE_DATA — DENIED
```

Common DACL issues:

- **No matching allow ACE** — the process is not in any group that has access. Add an appropriate allow ACE.
- **A deny ACE matches** — the process is in a group that is explicitly denied. Remove the deny ACE or remove the process from the denied group.
- **ACE ordering** — a deny ACE appears after an allow ACE and never takes effect, or an allow ACE appears after a deny and is blocked. Check canonical ordering.
- **Deny-only groups** — the process holds administrative groups as deny-only (filtered token). The group matches deny ACEs but not allow ACEs. Elevate if the access requires administrative authority.

**Fix:** Modify the DACL to grant the appropriate access, or fix ACE ordering.

### 4. Privilege overrides (or lack thereof)

**Symptom:** A process expects a privilege to grant access (backup, restore, take ownership) but the privilege is not enabled.

**Check:**

```bash
$ idn privileges 1482
SeBackupPrivilege                        disabled
```

**Fix:** Enable the privilege before the operation:

```bash
$ idn privilege enable SeBackupPrivilege
```

Remember that backup and restore privileges are intent-gated — the operation must declare backup/restore intent for the privilege to take effect.

### 5. Restricted token

**Symptom:** The normal DACL evaluation would grant access, but the process has restricting SIDs that do not match any allow ACE.

**Check:**

```bash
$ idn show 1482
...
Restricted:   yes

Restricting SIDs:
  app-sandbox
```

The DACL is walked twice — the second walk uses only restricting SIDs. Both must grant the requested rights.

**Fix:** Add an allow ACE for the restricting SID to the object's DACL, or use a less-restricted token.

### 6. Confinement

**Symptom:** A confined process is denied access to an object that the user's identity would normally be able to access.

**Check:**

```bash
$ idn show 3201
...
Confined:     yes
Confinement SID: S-1-15-2-394857203
```

The object's DACL must contain an ACE targeting the confinement SID, a capability SID, or ALL_APPLICATION_PACKAGES.

**Fix:** Add an appropriate ACE to the object's DACL, or use an unconfined process.

### 7. Central Access Policy

**Symptom:** Access is denied even though the object's own DACL grants it. The denial comes from a centrally-defined policy.

**Check:**

```bash
$ sd cap list /srv/data/reports
Applied policies:
  Finance Data Policy          S-1-17-...-1001   (effective)
```

**Fix:** The policy is defined centrally — modify the policy definition, not the object's DACL. Or check whether the policy is missing from the cache (recovery policy may be too restrictive).

## Impersonation issues

If a service thread is getting unexpected access denials, check whether it is impersonating:

```bash
$ idn show 1482/1509
Impersonating:   yes
Impersonation Level: Identification
```

At **Identification** level, the service can see the client's identity but cannot act as them — access decisions use the Anonymous identity. The client may need to connect at Impersonation level.

Also check whether the thread is impersonating at all:

```bash
$ idn show 1482/1509
Impersonating:   no
```

If the service forgot to impersonate, it is accessing resources under its own identity — which may not have the access the client would have.
