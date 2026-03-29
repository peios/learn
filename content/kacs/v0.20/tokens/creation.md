---
title: Token Creation
order: 4
---

Tokens are created through three operations, each serving a different purpose.

## CreateToken

Mint a new token from scratch. The caller provides the security-meaningful content; the kernel generates internal bookkeeping and validates structural invariants.

**Gated by:** `SeCreateTokenPrivilege`.

**Caller-supplied fields:** `user_sid`, `groups` (with attributes), privileges (which to grant), `owner_sid`, `primary_group_sid`, `default_dacl`, `integrity_level`, `mandatory_policy`, `token_type`, `impersonation_level`, `auth_id` (MUST reference an existing logon session), claims, device identity, confinement settings, credential projection data, source.

**Kernel-generated fields:** `token_id` (LUID), `modified_id` (initialized to `token_id`), `created_at` (current time), token SD (default SD per the Token Access Rights section).

The kernel validates:

1. The caller holds `SeCreateTokenPrivilege`.
2. All SIDs are structurally well-formed.
3. The owner SID is the user SID or a group with SE_GROUP_OWNER. Resolved to `owner_sid_index`.
4. The primary group SID is the user SID or a group SID on the token. Resolved to `primary_group_index`.
5. The `auth_id` references an existing logon session object.

The kernel MUST NOT authenticate the user, look up SIDs in the directory, resolve SID-to-UID mappings, or validate that the principal exists. The caller is trusted as TCB by virtue of holding `SeCreateTokenPrivilege`.

Returns a token file descriptor to the caller.

## DuplicateToken

Create an independent copy of an existing token.

**Requires:** `TOKEN_DUPLICATE` access on the source token.

The caller MAY change during duplication:

- **Token type** — primary to impersonation, or impersonation to primary.
- **Impersonation level** — equal to or lower than the source token's level (if creating an impersonation token). Escalation is forbidden — an Identification-level token MUST NOT be duplicated as Impersonation.
- **Token SD** — the new token's own security descriptor.

All other fields are copied verbatim. The `elevation_type` is reset to Default — the duplicate is not part of any linked elevation pair.

The new token receives its own `token_id`. The `modified_id` is reset. The original token is unaffected.

## FilterToken

Create a restricted copy of an existing token.

**Requires:** `TOKEN_DUPLICATE` access on the source token.

FilterToken MAY:

- **Remove privileges** — specified privileges are permanently deleted from the new token (cleared from the present, enabled, and enabled-by-default states).
- **Set groups to deny-only** — specified groups receive SE_GROUP_USE_FOR_DENY_ONLY. They can block access via deny ACEs but MUST NOT grant access via allow ACEs. This is permanent and MUST NOT be reverted.
- **Add restricted SIDs** — a secondary SID list added to the new token. AccessCheck evaluates the DACL twice on restricted tokens; access is granted only if both the normal SIDs and the restricted SIDs independently pass.
- **Enable write-restricted mode** — a flag that limits the restricted SID check to write operations only. Read access uses the normal SID list, bypassing the restricted evaluation.

FilterToken creates a new token object. The original is untouched. The `elevation_type` is reset to Default — the filtered token is not part of any linked elevation pair. The set of group SIDs is preserved: FilterToken changes per-group attribute flags and adds a separate restricted SID list, but MUST NOT add or remove SIDs from the group list itself.

A strictly confined token MUST NOT carry ALL_APPLICATION_PACKAGES in its `confinement_capabilities`. Token construction MUST enforce this invariant.
