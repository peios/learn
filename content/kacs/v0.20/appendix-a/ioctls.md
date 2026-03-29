---
title: Token Ioctls
order: 2
---

Token fds support the following ioctls. Each fd carries a per-handle access mask that gates which ioctls the holder can call.

## KACS_IOC_QUERY

Queries token information. Takes a query class and output buffer. Uses the two-call pattern: call with `buf_len=0` to get the needed size, then call again.

Requires TOKEN_QUERY (0x0008).

| Query class | Returns |
|---|---|
| TokenUser | User SID. |
| TokenGroups | Array of (SID, attributes) pairs. |
| TokenPrivileges | Privilege state (present, enabled, default, used). |
| TokenOwner | Default owner SID for new objects. |
| TokenPrimaryGroup | Default primary group SID. |
| TokenDefaultDacl | Default DACL for new objects. |
| TokenSource | 8-byte name + source ID. |
| TokenType | Primary (1) or Impersonation (2). |
| TokenImpersonationLevel | Anonymous / Identification / Impersonation / Delegation. |
| TokenStatistics | Token ID, logon session ID, modified ID, token type, expiration. |
| TokenRestrictedSids | Restricting SID array. |
| TokenSessionId | Interactive session ID. |
| TokenOrigin | Originating logon session ID. |
| TokenElevationType | Default (1) / Full (2) / Limited (3). |
| TokenIntegrityLevel | Mandatory integrity SID. |
| TokenMandatoryPolicy | NO_WRITE_UP, NEW_PROCESS_MIN flags. |
| TokenLogonType | Interactive / Service / Network / etc. |
| TokenLogonSid | The session's logon SID (`S-1-5-5-X-Y`). |
| TokenDeviceGroups | Device group SIDs. |

## KACS_IOC_IMPERSONATE

Impersonates this token on the calling thread. The token MUST be an impersonation token. Follows the two-gate model.

Requires TOKEN_IMPERSONATE (0x0004).

## KACS_IOC_INSTALL

Commits this token as the calling process's primary token. The token MUST be a primary token. When the new token's user SID differs from the current primary token's, the process SD is automatically regenerated.

Requires TOKEN_ASSIGN_PRIMARY (0x0001) on the handle and SeAssignPrimaryTokenPrivilege on the caller's real token.

## KACS_IOC_DUPLICATE

Deep-clones the token into a new token fd. Takes: target token type, target impersonation level, and desired access mask for the new handle. Impersonation level escalation is forbidden. The duplicate's `elevation_type` is reset to Default.

Requires TOKEN_DUPLICATE (0x0002).

## KACS_IOC_ADJUST_PRIVS

Enables, disables, or removes privileges atomically. Takes an array of (privilege, action) pairs. Removal is irreversible. Bumps `modified_id`.

Requires TOKEN_ADJUST_PRIVILEGES (0x0020).

## KACS_IOC_ADJUST_GROUPS

Enables or disables group entries. Takes an array of (group, enable/disable) pairs. Mandatory groups MUST NOT be disabled. Bumps `modified_id`.

Requires TOKEN_ADJUST_GROUPS (0x0040).

## KACS_IOC_RESTRICT

Creates a restricted token. Takes: SIDs to mark deny-only, privileges to remove, and restricting SIDs to add. Returns a new token fd. The restricted token's `elevation_type` is reset to Default.

Requires TOKEN_DUPLICATE (0x0002).

## KACS_IOC_LINK_TOKENS

Associates an elevated/filtered token pair on a logon session. Both tokens MUST belong to the same logon session. The pair is registered at the session level.

Requires SeTcbPrivilege.

## KACS_IOC_GET_LINKED_TOKEN

Retrieves the partner token from a linked pair. Returns a deep clone at Identification level with TOKEN_QUERY access only. The caller can inspect the partner but MUST NOT impersonate it.

Requires TOKEN_QUERY (0x0008).
