---
title: Token Ioctls
---

Token fds support the following ioctls. Each fd carries a per-handle access mask that gates which ioctls the holder can call.

All token fds are created with `O_CLOEXEC` set. Token fds MUST NOT be inherited across `execve()` by default. A process that needs to pass a token fd to a child across exec MUST explicitly clear `FD_CLOEXEC` via `fcntl(F_SETFD)`. This matches the Windows model where handles are not inherited by default.

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
| TokenStatistics | Token GUID, LogonSession ID, modified ID, token type, expiration. |
| TokenRestrictedSids | Restricting SID array. |
| TokenInteractivityScope | Interactivity scope number. |
| TokenOrigin | Originating LogonSession ID. |
| TokenElevationType | Default (1) / Full (2) / Limited (3). |
| TokenIntegrityLevel | Mandatory integrity SID. |
| TokenMandatoryPolicy | NO_WRITE_UP, NEW_PROCESS_MIN flags. |
| TokenLogonType | Logon type from the token's LogonSession (looked up via `auth_id` in the LogonSession table). |
| TokenLogonSid | The LogonSession's logon SID (`S-1-5-5-X-Y`). |
| TokenDeviceGroups | Device group SIDs. |
| TokenAppContainerSid | Confinement SID (empty if not confined). |
| TokenCapabilities | Confinement capability SIDs. |
| TokenUserClaims | The token's user-claim array using the standard KACS claim-array wrapper. |
| TokenDeviceClaims | The token's device-claim array using the standard KACS claim-array wrapper. |
| TokenProjectedSupplementaryGids | The token's projected Linux supplementary GID array. |

## KACS_IOC_IMPERSONATE

Impersonates this token on the calling thread. The token MUST be an impersonation token. Follows the two-gate model with the calling thread's primary token (real_cred) as the "server" and the fd's token as the "client":

- **Gate 1 (identity)**: server user SID == client user SID with same restriction status, OR server holds SeImpersonatePrivilege. Restriction mismatch (restricted server → unrestricted client) is hard-denied (-EPERM). Other identity gate failures cap to Identification level.
- **Gate 2 (integrity ceiling)**: effective level is capped if client integrity > server integrity.

The effective impersonation level is the minimum of: the token's own impersonation_level and the level permitted by the gates.

Requires TOKEN_IMPERSONATE (0x0004).

## KACS_IOC_INSTALL

Commits this token as the calling process's primary token. The token MUST be a
primary token.

The install is process-wide, not thread-local: the kernel replaces the primary
token for the entire calling thread group.

- Threads that are not impersonating switch immediately to the new primary
  token as both `real_cred` and `cred`.
- Threads that are currently impersonating keep their active impersonation in
  `cred`; only `real_cred` changes underneath them. A later `kacs_revert()`
  lands on the new primary token, not the old one.
- The calling thread performs its install immediately. Sibling threads in the
  same thread group converge in their own context via queued in-kernel
  credential work. A brief transition window where some sibling threads still
  observe the old primary token is permitted. No completion barrier is exposed
  to the caller.

When the new token's user SID differs from the current primary token's, the
process SD is automatically regenerated using the default template with the new
token's user SID as owner. If the user SID does not change, the existing
process SD is preserved.

### Requirements

- TOKEN_ASSIGN_PRIMARY (0x0001) on the handle.
- SeAssignPrimaryTokenPrivilege on the caller's real token.
- The new token's user SID MUST match the caller's current primary token's user SID, unless the caller has SeTcbPrivilege.
- The new token MUST belong to the same LogonSession (matching `auth_id`) as the caller's current primary token, unless the caller has SeTcbPrivilege.
- The new token's LogonSession MUST NOT be dead.

The SID and LogonSession constraints prevent a non-TCB holder of SeAssignPrimaryTokenPrivilege from installing an arbitrary high-privilege token on itself. SeTcbPrivilege bypasses the SID and LogonSession-matching constraints — this is the mechanism peinit uses when installing service tokens with different user SIDs. The dead-LogonSession check is unconditional (SeTcbPrivilege does not bypass it).

## KACS_IOC_DUPLICATE

Deep-clones the token into a new token fd. Takes: target token type, target impersonation level, and desired access mask for the new handle. Impersonation level escalation is forbidden only when the source token is already an impersonation token (new level MUST be <= source level in that case). A primary token duplicated to Impersonation MAY use any caller-selected impersonation level. When duplicating to Primary, impersonation_level is set to Anonymous. The duplicate's `elevation_type` is reset to Default. The `modified_id` is initialized to the new `token_id`.

When the target impersonation level is Anonymous, the duplicate is stripped to a minimal Anonymous token: user SID = `S-1-5-7`, no groups (except Everyone per system policy), no privileges, integrity = Untrusted. The source token's identity is not carried forward. See §9.3 for the full Anonymous semantics.

The desired access mask for the new handle is checked against the new token's SD (which is a freshly generated default SD). The caller's effective token is the subject for this AccessCheck.

Requires TOKEN_DUPLICATE (0x0002) on the source handle.

## KACS_IOC_ADJUST_PRIVS

Enables, disables, removes, or resets privileges atomically. Takes an array of
(privilege, action) pairs. Removal is irreversible.

Special sentinel: if the first and only entry is
`{ luid = 0, attributes = KACS_PRIV_RESET_ALL_DEFAULTS }`,
`privileges_enabled` is reset to `privileges_enabled_by_default`.
Reset-to-defaults does NOT restore removed privileges: privileges absent from
`privileges_present` remain absent. Any other use of
`KACS_PRIV_RESET_ALL_DEFAULTS` is invalid. Unknown `attributes` bits are
invalid. Duplicate privilege indices in the same request are invalid. All
entries are validated before any are applied. Enabling a privilege that is
absent from `privileges_present` is invalid; disabling or removing an already
absent privilege is a no-op.

Bumps `modified_id`.

Requires TOKEN_ADJUST_PRIVILEGES (0x0020).

## KACS_IOC_ADJUST_GROUPS

Enables or disables group entries atomically. Takes an array of
(group index, enable/disable) pairs. Group indices are zero-based into the
token's groups array. `count = 0` is invalid. All entries are validated before
any are applied — if any entry targets a mandatory, deny-only, or logon SID
group, or if any group index appears more than once in the same request, the
entire operation fails with no changes.

Special sentinel: if the first entry has `index = 0xFFFFFFFF` and `enable = 0`,
all groups are reset to their creation-time enabled/disabled state. The
sentinel MUST be the only entry (`count = 1`). Any other use of
`index = 0xFFFFFFFF` is invalid.

Reset does NOT undo deny-only status set by FilterToken —
`SE_GROUP_USE_FOR_DENY_ONLY` groups remain deny-only. Bumps `modified_id`.

Requires TOKEN_ADJUST_GROUPS (0x0040).

## KACS_IOC_ADJUST_INTERACTIVITY_SCOPE

Changes the token's interactivity scope. Takes a `u32` scope value.

Requires TOKEN_ADJUST_INTERACTIVITY_SCOPE (0x0100) on the handle and SeTcbPrivilege on the caller's real token. Bumps `modified_id`.

## KACS_IOC_ADJUST_DEFAULT

Adjusts the token's default owner, primary group, and/or default DACL. Takes a struct with: `dacl_ptr` (userspace pointer to new default DACL, 0 = no change), `dacl_len` (length, 0 with non-null ptr = clear DACL), `owner_index` (new owner_sid_index, `0xFFFF` = no change), `group_index` (new primary_group_index, `0xFFFF` = no change). Each field is independently optional. Bumps `modified_id`.

Requires TOKEN_ADJUST_DEFAULT (0x0080).

## KACS_IOC_RESTRICT

Creates a restricted token. Takes: SIDs to mark deny-only, privileges to remove, restricting SIDs to add, and a `write_restricted` flag. The variable payload at `data_ptr` is `u32[num_deny_indices]` immediately followed by `num_restrict_sids` packed binary SIDs. Deny indices are zero-based into the token's group array. Duplicate deny indices are invalid. `data_len` MUST match this layout exactly: truncated, malformed, or trailing payload bytes are invalid. All inputs are validated before any token is created; if any index or SID entry is invalid, the operation fails with no result token. When `write_restricted` is set, the restricted SID check applies only to write operations and `user_deny_only` is set to true. Returns a new token fd with the same per-handle access mask as the source token fd used for this ioctl. The restricted token's `elevation_type` is reset to Default.

Requires TOKEN_DUPLICATE (0x0002).

## KACS_IOC_LINK_TOKENS

Associates an elevated/filtered token pair on a LogonSession. Takes a struct with two token fds: `elevated_fd` (first) and `filtered_fd` (second), plus a `logon_session_id`. Both tokens MUST belong to the specified LogonSession, MUST be primary tokens, and MUST carry the same user SID. The pair is registered at the LogonSession level. Upon successful linking, the elevated token's `elevation_type` is set to Full and the filtered token's `elevation_type` is set to Limited. This is the only mechanism that sets elevation_type to a non-Default value.

Requires SeTcbPrivilege. Both token fds require TOKEN_DUPLICATE access. "Belongs to" means the token's `auth_id` equals the specified `logon_session_id` (LUID comparison). The `logon_session_id` parameter is a `u64` LUID. Linking tokens that are already part of a pair replaces the existing pair on that session. Linking a token to itself returns `-EINVAL`. If a token already has `elevation_type = Full`, it MAY be relinked only in the `elevated_fd` role. If a token already has `elevation_type = Limited`, it MAY be relinked only in the `filtered_fd` role. Role changes fail with `-EINVAL`.

## KACS_IOC_GET_LINKED_TOKEN

Retrieves the partner token from a linked pair. Behavior depends on privilege:

- **Without SeTcbPrivilege:** returns a deep clone at Identification impersonation level with TOKEN_QUERY access only. The clone follows DuplicateToken semantics for independent object creation (new token object, new `token_id`, `modified_id` initialized to the new `token_id`, fresh default token SD), except that it preserves the partner token's `elevation_type`. The caller can inspect the partner's identity but MUST NOT impersonate it or use it for access decisions.
- **With SeTcbPrivilege:** returns a full primary token handle to the actual linked token. The caller receives full usability — this is required for system daemons (authd) that manage linked pairs.

Requires TOKEN_QUERY (0x0008). If the token is not part of a linked pair (elevation_type is Default, or the pair was destroyed by LogonSession termination), returns `-ENOENT`.

> [!INFORMATIVE]
> Returning TOKEN_QUERY via TOKEN_QUERY (rather than requiring TOKEN_DUPLICATE) is an intentional exception to the normal handle model. This matches the Windows `TokenLinkedToken` query behavior.
