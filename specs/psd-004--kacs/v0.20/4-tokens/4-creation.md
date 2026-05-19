---
title: Token Creation
---

Tokens are created through three operations, each serving a different purpose.

## CreateToken

Mint a new token from scratch. The caller provides the security-meaningful content; the kernel generates internal bookkeeping and validates structural invariants.

**Gated by:** `SeCreateTokenPrivilege`.

**Caller-supplied fields:** `user_sid`, `groups` (with attributes), privileges (`privs_present` + `privs_enabled`), `owner_sid_index`, `primary_group_index`, `default_dacl`, `integrity_level`, `mandatory_policy`, `token_type`, `impersonation_level`, `auth_id` (MUST reference an existing logon session), `expiration` (0 = no expiry), `audit_policy`, `source` (name + LUID), `user_claims`, `device_claims`, `device_groups`, `restricted_sids`, `restricted_device_groups`, `confinement_sid`, `confinement_capabilities`, `confinement_exempt`, `isolation_boundary`, `write_restricted`, `user_deny_only`, `projected_uid`, `projected_gid`, `projected_supplementary_gids`, `origin`, `interactive_session_id`. See §13.6 for the complete wire format.

**Kernel-generated fields:** `token_id` (LUID), `modified_id` (initialized to `token_id`), `created_at` (current time), `elevation_type` (always Default), `logon_sid` (derived from `session_id` as `S-1-5-5-{session_id >> 32}-{session_id & 0xFFFFFFFF}`), token SD (default SD per §4.8).

The kernel injects the logon SID into the groups array with `SE_GROUP_MANDATORY | SE_GROUP_ENABLED_BY_DEFAULT | SE_GROUP_ENABLED | SE_GROUP_LOGON_ID`. Callers MUST NOT include the logon SID in their supplied groups array — it is always kernel-generated. The injected entry is appended after the caller's groups. `owner_sid_index` and `primary_group_index` are interpreted relative to the caller-supplied groups (0 = user SID, 1..N = caller's groups), not including the kernel-injected logon SID entry.

The kernel validates:

1. The caller holds `SeCreateTokenPrivilege`.
2. All SIDs are structurally well-formed.
3. The owner SID is the user SID or a group with SE_GROUP_OWNER. Resolved to `owner_sid_index`.
4. The primary group SID is the user SID or a group SID on the token. Resolved to `primary_group_index`.
5. The `auth_id` references an existing logon session object.
6. If `token_type` is Primary, `impersonation_level` MUST be Anonymous.
7. If `write_restricted` is true, `user_deny_only` MUST be true.
8. If `isolation_boundary` is true, `confinement_sid` MUST be present.
9. `elevation_type` field in the wire format MUST be 0 (reserved). The kernel always sets Default.
10. The caller-supplied group count plus the kernel-injected logon SID MUST
    fit the 64-entry token group limit.

The kernel MUST NOT authenticate the user, look up SIDs in the directory, resolve SID-to-UID mappings, or validate that the principal exists. The caller is trusted as TCB by virtue of holding `SeCreateTokenPrivilege`.

Returns a token file descriptor to the caller. Because CreateToken does not
take a desired-access parameter, the returned handle always carries the fixed
cached access mask `TOKEN_ALL_ACCESS`.

## DuplicateToken

Create an independent copy of an existing token.

**Requires:** `TOKEN_DUPLICATE` access on the source token.

The caller MAY change during duplication:

- **Token type** — primary to impersonation, or impersonation to primary. When duplicating to Primary, the `impersonation_level` MUST be set to Anonymous.
- **Impersonation level** — when the source token is an impersonation token and the duplicate target type is also Impersonation, the new level MUST be equal to or lower than the source token's level. Escalation is forbidden — an Identification-level impersonation token MUST NOT be duplicated as Impersonation or Delegation. When the source token is Primary and the duplicate target type is Impersonation, the caller MAY choose any impersonation level.



Fields on the new token:

- `token_id` — new LUID.
- `modified_id` — initialized to the new `token_id`.
- `token_type` — caller-specified (Primary or Impersonation).
- `impersonation_level` — caller-specified for Impersonation. If the source token is an impersonation token, the new level must be <= the source level. If the source token is Primary, any impersonation level is valid. Primary duplicates always use Anonymous.
- `elevation_type` — reset to Default (not part of any linked pair).
- `user_sid`, `user_deny_only`, `logon_sid` — copied from source.
- `groups` — copied from source (SIDs and all per-group attributes).
- `restricted_sids`, `write_restricted` — copied from source.
- `privileges` — present/enabled/enabled_by_default copied from source. `used` copied from source.
- `integrity_level`, `mandatory_policy` — copied from source.
- `auth_id`, `origin`, `source`, `created_at`, `expiration`, `audit_policy` — copied from source.
- `interactive_session_id` — copied from source.
- `default_dacl`, `owner_sid_index`, `primary_group_index` — copied from source.
- `user_claims`, `device_claims`, `device_groups`, `restricted_device_groups` — copied from source.
- `confinement_sid`, `confinement_capabilities`, `confinement_exempt` — copied from source.
- `projected_uid`, `projected_gid`, `projected_supplementary_gids` — copied from source.
- Token SD — new default SD per §4.8. The caller cannot supply a custom SD at duplication time; use WRITE_DAC on the new handle to modify afterward if needed.

The original token is unaffected.

## FilterToken

Create a restricted copy of an existing token.

**Requires:** `TOKEN_DUPLICATE` access on the source token.

FilterToken MAY:

- **Remove privileges** — specified privileges are permanently deleted from the new token (cleared from the present, enabled, and enabled-by-default states).
- **Set groups to deny-only** — specified groups receive SE_GROUP_USE_FOR_DENY_ONLY. They can block access via deny ACEs but MUST NOT grant access via allow ACEs. This is permanent and MUST NOT be reverted.
- **Add restricted SIDs** — a secondary SID list added to the new token. AccessCheck evaluates the DACL twice on restricted tokens; access is granted only if both the normal SIDs and the restricted SIDs independently pass.
- **Enable write-restricted mode** — a flag that limits the restricted SID check to write operations only. Read access uses the normal SID list, bypassing the restricted evaluation. When write-restricted mode is enabled, `user_deny_only` MUST be set to true on the new token — the user SID matches only deny ACEs.

FilterToken input validation is all-or-nothing. The deny-only list uses
zero-based group indices into the source token's group array; duplicate or
out-of-range indices are invalid. The restricting SID blob MUST parse exactly
as the declared packed SID list, with no truncated or trailing bytes. If any
entry is malformed, no token is created.

If the source token is already restricted and the intersection of the source
restricted SID list with the provided restricting SID list is empty, the
request is invalid and no token is created.

FilterToken creates a new token object. The original is untouched. Fields on the new token:

- `token_id` — new LUID.
- `modified_id` — initialized to the new `token_id`.
- `elevation_type` — reset to Default (not part of any linked pair).
- `user_sid`, `logon_sid`, `integrity_level`, `mandatory_policy`, `token_type`, `impersonation_level` — copied from source.
- `groups` — SIDs copied from source. Per-group attributes modified per the deny-only list. No SIDs added or removed.
- `privileges` — present/enabled/enabled_by_default modified per the removal list. `used` reset to 0.
- `restricted_sids` — set from the provided restricting SID list. If the source was already restricted, the new list is the intersection of source and provided lists.
- `write_restricted` — set if requested, OR sticky from source (`write_restricted || source.write_restricted`).
- `user_deny_only` — set to true when write_restricted is enabled, false otherwise.
- `auth_id`, `origin`, `source`, `created_at`, `expiration`, `audit_policy` — copied from source.
- `default_dacl`, `owner_sid_index`, `primary_group_index` — copied from source.
- `user_claims`, `device_claims`, `device_groups`, `restricted_device_groups` — copied from source.
- `confinement_sid`, `confinement_capabilities`, `confinement_exempt` — copied from source.
- `projected_uid`, `projected_gid`, `projected_supplementary_gids` — copied from source.
- Token SD — new default SD per §4.8.

KACS treats `confinement_capabilities` as caller-supplied SID values after
structural SID validation. Strict confinement is represented by the caller
omitting ALL_APPLICATION_PACKAGES from that list. The kernel MUST NOT synthesize
ALL_APPLICATION_PACKAGES, and it MUST NOT reject an otherwise valid normal
confined token merely because ALL_APPLICATION_PACKAGES is present. Authd and
policy tooling are responsible for deciding which confinement capabilities a
package token receives.
