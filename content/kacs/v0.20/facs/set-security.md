---
title: The Set-Security Interface
order: 6
---

All SD modification flows through a single KACS syscall. The caller provides a file descriptor or path, a bitmask specifying which SD components to modify, and a self-relative SD blob containing the new values.

## Security information flags

| Flag | Component | Required right |
|---|---|---|
| OWNER_SECURITY_INFORMATION | Owner SID | WRITE_OWNER |
| GROUP_SECURITY_INFORMATION | Group SID | WRITE_OWNER |
| DACL_SECURITY_INFORMATION | Discretionary ACL | WRITE_DAC |
| SACL_SECURITY_INFORMATION | System ACL | ACCESS_SYSTEM_SECURITY |
| LABEL_SECURITY_INFORMATION | Mandatory integrity label | WRITE_OWNER + integrity constraints |

The kernel validates the SD blob structurally (parseable, well-formed ACEs, valid SIDs, size within 64 KB) then merges only the indicated components into the existing SD. Unindicated components are preserved unchanged.

MIC and PIP apply to these checks. A low-integrity caller MUST NOT modify a high-integrity file's SD even if the DACL grants WRITE_OWNER.

## Ownership constraints

When setting a new owner, the caller MAY only set the owner to:

- Their own SID.
- A group SID on the token with SE_GROUP_OWNER.

SeTakeOwnershipPrivilege allows setting ownership to the caller's own SID regardless of the current SD. SeRestorePrivilege allows setting ownership to any arbitrary SID.

## Integrity label constraints

Without SeRelabelPrivilege, callers MAY only set a label at or below their own integrity level. With SeRelabelPrivilege, any level is permitted.

## SeRestorePrivilege bypass

SeRestorePrivilege bypasses the access check entirely. Same syscall, same interface, no special code path — the privilege fires in the AccessCheck pipeline and grants all requested rights. This is the mechanism for backup restoration, administrative SD repair, and the missing-SD repair path.

## Write mechanics

After merging:

1. Serialize the updated SD to self-relative binary format.
2. Write the appropriate xattr via an internal kernel path that bypasses the setxattr denial hook.
3. Update the in-memory SD cache in the same operation.
4. Emit an audit event if the file's SACL contains a matching audit ACE.

Concurrent set-security calls on the same inode are serialized by the inode mutex. RCU readers on the AccessCheck path are not blocked.
