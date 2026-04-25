---
title: Token Ioctls
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
| TokenImpersonationLevel | Anonymous / Identification / Impersonation / Delegation. Primary tokens return Anonymous. |
| TokenStatistics | Token ID, logon session ID, modified ID, token type, expiration. |
| TokenRestrictedSids | Restricting SID array. |
| TokenSessionId | Interactive session ID. |
| TokenOrigin | Originating logon session ID. |
| TokenElevationType | Default (1) / Full (2) / Limited (3). |
| TokenIntegrityLevel | Mandatory integrity SID. |
| TokenMandatoryPolicy | NO_WRITE_UP, NEW_PROCESS_MIN flags. |
| TokenLogonType | Logon type from the token's logon session (looked up via `auth_id` in the session table). |
| TokenLogonSid | The session's logon SID (`S-1-5-5-X-Y`). |
| TokenDeviceGroups | Device group SIDs. |
| TokenAppContainerSid | Confinement SID (empty if not confined). |
| TokenCapabilities | Confinement capability SIDs. |

## KACS_IOC_IMPERSONATE

Impersonates this token on the calling thread. The token MUST be an impersonation token. Follows the two-gate model with the calling thread's primary token (real_cred) as the "server" and the fd's token as the "client":

- **Gate 1 (identity)**: server user SID == client user SID with same restriction status, OR server holds SeImpersonatePrivilege. Restriction mismatch (restricted server → unrestricted client) is hard-denied (-EPERM). Other identity gate failures cap to Identification level.
- **Gate 2 (integrity ceiling)**: effective level is capped if client integrity > server integrity.

The effective impersonation level is the minimum of: the token's own impersonation_level and the level permitted by the gates.

Requires TOKEN_IMPERSONATE (0x0004).

## KACS_IOC_INSTALL

Commits this token as the calling process's primary token. The token MUST be a primary token. When the new token's user SID differs from the current primary token's, the process SD is automatically regenerated using the default template with the new token's user SID as owner.

Requires TOKEN_ASSIGN_PRIMARY (0x0001) on the handle and SeAssignPrimaryTokenPrivilege on the caller's real token.

## KACS_IOC_DUPLICATE

Deep-clones the token into a new token fd. Takes: target token type, target impersonation level, and desired access mask for the new handle. Impersonation level escalation is forbidden (new level MUST be <= source level for impersonation tokens). When duplicating to Primary, impersonation_level is set to Anonymous. The duplicate's `elevation_type` is reset to Default. The `modified_id` is initialized to the new `token_id`.

The desired access mask for the new handle is checked against the new token's SD (which is a freshly generated default SD). The caller's effective token is the subject for this AccessCheck.

Requires TOKEN_DUPLICATE (0x0002) on the source handle.

## KACS_IOC_ADJUST_PRIVS

Enables, disables, or removes privileges atomically. Takes an array of (privilege, action) pairs. Removal is irreversible. Bumps `modified_id`.

Requires TOKEN_ADJUST_PRIVILEGES (0x0020).

## KACS_IOC_ADJUST_GROUPS

Enables or disables group entries atomically. Takes an array of (group index, enable/disable) pairs. All entries are validated before any are applied — if any entry targets a mandatory, deny-only, or logon SID group, the entire operation fails with no changes. Special sentinel: if the first entry has `index = 0xFFFFFFFF`, all groups are reset to their creation-time enabled/disabled state. The sentinel MUST be the only entry (`count = 1`). Reset does NOT undo deny-only status set by FilterToken — SE_GROUP_USE_FOR_DENY_ONLY groups remain deny-only. Bumps `modified_id`.

Requires TOKEN_ADJUST_GROUPS (0x0040).

## KACS_IOC_ADJUST_SESSIONID

Changes the token's interactive session ID. Takes a `u32` session ID value.

Requires TOKEN_ADJUST_SESSIONID (0x0100) on the handle and SeTcbPrivilege on the caller's real token. Bumps `modified_id`.

## KACS_IOC_ADJUST_DEFAULT

Adjusts the token's default owner, primary group, and/or default DACL. Takes a struct with: `dacl_ptr` (userspace pointer to new default DACL, 0 = no change), `dacl_len` (length, 0 with non-null ptr = clear DACL), `owner_index` (new owner_sid_index, `0xFFFF` = no change), `group_index` (new primary_group_index, `0xFFFF` = no change). Each field is independently optional. Bumps `modified_id`.

Requires TOKEN_ADJUST_DEFAULT (0x0080).

## KACS_IOC_RESTRICT

Creates a restricted token. Takes: SIDs to mark deny-only, privileges to remove, restricting SIDs to add, and a `write_restricted` flag. When `write_restricted` is set, the restricted SID check applies only to write operations and `user_deny_only` is set to true. Returns a new token fd. The restricted token's `elevation_type` is reset to Default.

Requires TOKEN_DUPLICATE (0x0002).

## KACS_IOC_LINK_TOKENS

Associates an elevated/filtered token pair on a logon session. Takes a struct with two token fds: `elevated_fd` (first) and `filtered_fd` (second), plus a `session_id`. Both tokens MUST belong to the specified logon session. The pair is registered at the session level. Upon successful linking, the elevated token's `elevation_type` is set to Full and the filtered token's `elevation_type` is set to Limited. This is the only mechanism that sets elevation_type to a non-Default value.

Requires SeTcbPrivilege. Both token fds require TOKEN_DUPLICATE access. "Belongs to" means the token's `auth_id` equals the specified `session_id` (LUID comparison). The `session_id` parameter is a `u64` LUID. Linking tokens that are already part of a pair replaces the existing pair. Linking a token to itself returns `-EINVAL`.

## KACS_IOC_GET_LINKED_TOKEN

Retrieves the partner token from a linked pair. Behavior depends on privilege:

- **Without SeTcbPrivilege:** returns a deep clone at Identification impersonation level with TOKEN_QUERY access only. The caller can inspect the partner's identity but MUST NOT impersonate it or use it for access decisions.
- **With SeTcbPrivilege:** returns a full primary token handle to the actual linked token. The caller receives full usability — this is required for system daemons (authd) that manage linked pairs.

Requires TOKEN_QUERY (0x0008). If the token is not part of a linked pair (elevation_type is Default, or the pair was destroyed by session termination), returns `-ENOENT`.

> [!INFORMATIVE]
> Returning TOKEN_QUERY via TOKEN_QUERY (rather than requiring TOKEN_DUPLICATE) is an intentional exception to the normal handle model. This matches the Windows `TokenLinkedToken` query behavior.
