---
title: Understanding Restricted Tokens
type: concept
description: How restricted tokens use dual DACL evaluation with restricting SIDs to narrow access to an intersection of two checks.
---

A **restricted token** is a token with an additional set of **restricting SIDs**. When AccessCheck evaluates a restricted token, it walks the DACL **twice**: once using the token's normal SIDs, and once using only the restricting SIDs. Access is granted only if both evaluations agree.

This is a mechanism for narrowing access. A restricted token can never access more than the original token — it can only access the intersection of what the normal SIDs allow and what the restricting SIDs allow.

## Dual DACL evaluation

The two evaluations are independent:

| Evaluation | SIDs used | Must grant access? |
|---|---|---|
| **Normal** | User SID, group SIDs (as usual) | Yes |
| **Restricted** | Only the restricting SIDs | Yes |

Both must grant the requested rights. If the normal evaluation grants read and write, but the restricted evaluation only grants read, the result is read only. If either evaluation denies, the request is denied.

For example, a token with normal SID `alice` and restricting SID `read-only-workers` accessing a file:

```
DACL:
  Allow  alice              FILE_READ_DATA | FILE_WRITE_DATA
  Allow  read-only-workers  FILE_READ_DATA
```

Normal evaluation grants read and write (Alice matches). Restricted evaluation grants read only (`read-only-workers` matches for read but not write). The intersection: read only.

## Deny-only groups

When creating a restricted token, groups can be set to **deny-only**. A deny-only group remains in the token but can only match deny ACEs — it never matches allow ACEs.

This is how the filtered token in a linked token pair works. When an administrative user authenticates, their filtered token has administrative groups set to deny-only:

- If an object has a deny ACE targeting Administrators, the deny still applies — the group matches
- If an object has an allow ACE targeting Administrators, the allow is ignored — the group cannot grant access

The group is visible but not exercisable. The user's administrative membership can cause them to be denied access but cannot cause them to be granted access.

## Write-restricted tokens

A **write-restricted** token is a variant where the second DACL evaluation only applies to write operations. Read and execute access is evaluated normally (using only the regular SIDs). Write access requires both evaluations to agree.

This is useful for processes that need broad read access but should have their write access narrowed — for example, a service that reads from many locations but should only write to a specific directory.

## Creating restricted tokens with FilterToken

Restricted tokens are created by **filtering** an existing token. A FilterToken operation can:

- **Remove privileges** — permanently strip privileges from the new token
- **Set groups to deny-only** — administrative groups remain visible but cannot grant access
- **Add restricting SIDs** — create the dual-evaluation constraint
- **Disable the no_child_process flag** — prevent the process from creating children

The result is always a new token that is **less powerful** than the original. FilterToken cannot add privileges, add group memberships, or raise the integrity level. The restricted token can do a subset of what the original could do — never more.

## How restriction differs from confinement

Both restriction and confinement narrow access via a second evaluation, but they work differently:

| | Restriction | Confinement |
|---|---|---|
| **Second evaluation uses** | Restricting SIDs | Confinement SID + capability SIDs |
| **Normal SIDs in second evaluation** | Ignored | Ignored |
| **Privileges bypass it** | Yes (privileges apply normally) | No (privileges are suppressed) |
| **Owner implicit rights** | Apply normally | Skipped |

Confinement is a stronger sandbox — it suppresses privileges and owner rights. Restriction is a narrowing mechanism that works within the normal access control model.
