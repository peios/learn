---
title: Token Structure
---

A token carries identity, policy, and metadata fields. Fields are organized by concern and annotated with mutability:

- **Fixed** — set at creation, never changes. The security-critical identity fields fall into this category.
- **Adjustable** — may be modified at runtime via the adjustment operations defined in this specification.
- **One-way** — can be set or tightened but never cleared or loosened.

## Identity core (fixed)

| Field | Type | Description |
|---|---|---|
| `user_sid` | SID | The token's primary identity. |
| `user_deny_only` | bool | If true, the user SID matches only deny ACEs, not allow ACEs. Set at creation (CreateToken or FilterToken). MUST be true when `write_restricted` is true. |
| `groups` | SID_AND_ATTRIBUTES[] | Group memberships. The set of SIDs is fixed at creation; per-group attribute flags are adjustable (see below). |
| `logon_sid` | SID | Per-authentication-event SID (`S-1-5-5-X-Y`). Ties the token to its LogonSession. This SID also appears in the `groups` array with `SE_GROUP_LOGON_ID` set — the standalone field is a convenience reference to the same SID. |
| `restricted_sids` | SID_AND_ATTRIBUTES[]? | Secondary SID list for restricted tokens. Null on unrestricted tokens. Set at creation (CreateToken or FilterToken). AccessCheck treats this list as presence-based: a restricting SID participates whenever it is present in the list, and `SE_GROUP_ENABLED` / `SE_GROUP_USE_FOR_DENY_ONLY` do not affect restricted-pass matching. |
| `write_restricted` | bool | If true, the restricted SID check applies only to write access. Set at creation (CreateToken or FilterToken). |

The set of group SIDs on a token is fixed at creation — AdjustGroups MUST NOT add or remove SIDs. However, individual groups MAY be enabled or disabled by modifying SE_GROUP_ENABLED, subject to constraints: mandatory groups (SE_GROUP_MANDATORY) MUST NOT be disabled, and deny-only groups (SE_GROUP_USE_FOR_DENY_ONLY) MUST NOT be re-enabled.

## Token type (fixed)

| Field | Type | Description |
|---|---|---|
| `token_type` | enum | Primary or Impersonation. |
| `impersonation_level` | enum | Anonymous, Identification, Impersonation, or Delegation. Primary tokens MUST have `impersonation_level` set to Anonymous. |

## Integrity (fixed)

| Field | Type | Description |
|---|---|---|
| `integrity_level` | uint | Numeric integrity level. Standard values: 0 (Untrusted), 4096 (Low), 8192 (Medium), 12288 (High), 16384 (System). Any unsigned integer is valid — compared numerically against object labels. |
| `mandatory_policy` | flags | NO_WRITE_UP (0x0001), NEW_PROCESS_MIN (0x0002). Per-token MIC enforcement policy. Set at creation time. |

The `mandatory_policy` field is immutable. A process MUST NOT change its MIC constraints at runtime (neither loosen nor tighten).

> [!INFORMATIVE]
> This is an intentional divergence. The reference model allows runtime modification of the mandatory policy, which reduces MIC to a constraint that only stops processes that do not actively try to bypass it. Immutability ensures MIC is a real security boundary.

## Privileges (adjustable)

A token MUST carry a set of privileges. Each privilege MUST have four independent states:

- **Present** — the privilege exists on the token. A present privilege MAY be removed (permanent), but a privilege MUST NOT be added after creation.
- **Enabled** — the privilege is currently active. Only present privileges MAY be enabled or disabled.
- **Enabled by default** — the creation-time enabled state. AdjustPrivileges MAY restore all privileges to this state.
- **Used** — the privilege has been exercised during this token's lifetime. Monotonic — once set, MUST NOT be cleared.

A privilege's lifecycle on a token: present and disabled → enabled → used → optionally disabled → optionally permanently removed. Removal clears the privilege from the present, enabled, and enabled-by-default states.

> [!INFORMATIVE]
> An implementation MAY encode these states as bitmasks (e.g., four 64-bit integers where each bit position corresponds to a defined privilege). This encoding provides constant-time privilege checks and atomic multi-privilege operations.

## Elevation (one-way)

| Field | Type | Description |
|---|---|---|
| `elevation_type` | enum | Default (non-elevated), Full (elevated), or Limited (filtered). Created as Default. Set to Full or Limited exclusively by KACS_IOC_LINK_TOKENS when a linked pair is established. Once set to Full or Limited, MUST NOT be changed back to Default. Reset to Default by DuplicateToken and FilterToken (the duplicate is not part of any linked pair). |

Linked token pairs are associated at the LogonSession level, not stored on individual tokens. See the Linked Tokens and Elevation section for the pairing mechanism.

## Default object security (adjustable)

| Field | Description |
|---|---|
| `owner_sid_index` | Index into [user_sid, groups...] selecting the default owner SID for new objects. 0 = user SID, 1..N = groups[0..N-1]. The referenced SID MUST be the user SID or a group with SE_GROUP_OWNER. |
| `primary_group_index` | Index into [user_sid, groups...] selecting the default primary group SID for new objects. 0 = user SID, 1..N = groups[0..N-1]. The referenced SID MUST be the user SID or a group SID on the token. |
| `default_dacl` | DACL applied to objects created by this token when no explicit SD is provided. |

> [!INFORMATIVE]
> An implementation MAY store the owner and primary group as indices into the token's SID arrays rather than as separate SID copies.

## Metadata (fixed)

| Field | Type | Description |
|---|---|---|
| `token_id` | LUID | Unique identifier for this token instance. |
| `auth_id` | LUID | LogonSession LUID. Links to the authentication event that produced this token. |
| `source` | TOKEN_SOURCE | Who minted this token. 8-character name + LUID. |
| `created_at` | timestamp | When the original token was minted by CreateToken. Copied unchanged by DuplicateToken, FilterToken, and NEW_PROCESS_MIN (tracks original minting time, not duplication time). |
| `expiration` | timestamp | When the token becomes invalid. Zero = no expiry. Not enforced by AccessCheck in v0.20. |
| `origin` | LUID | Originating LogonSession for derived tokens (S4U, network logon). |

## Mutation tracking (adjustable)

| Field | Description |
|---|---|
| `modified_id` | Counter incremented on any token adjustment. Serves as a cache invalidation key — if `modified_id` has changed since the last AccessCheck, cached decisions are stale. |

## Interactivity scope (adjustable)

| Field | Description |
|---|---|
| `interactivity_scope` | Interactivity scope number. 0 for services (no interactive environment), 1+ for interactive/remote user environments. Changing this field requires `SeTcbPrivilege`. |

## Claims and security attributes (fixed)

| Field | Type | Description |
|---|---|---|
| `user_claims` | CLAIM_ATTRIBUTES[] | Name-value pairs from the user's directory object. Fed into conditional ACE evaluation. |
| `device_claims` | CLAIM_ATTRIBUTES[] | Name-value pairs from the machine's directory object. |

## Device identity (fixed)

| Field | Type | Description |
|---|---|---|
| `device_groups` | SID_AND_ATTRIBUTES[]? | Machine's group memberships for compound identity. |
| `restricted_device_groups` | SID_AND_ATTRIBUTES[]? | Filtered device groups for restricted tokens. |

## Confinement (fixed)

| Field | Type | Description |
|---|---|---|
| `confinement_sid` | SID? | Puts the token in a default-deny sandbox. Null = not confined. When set, AccessCheck switches to default-deny: access requires explicit grant to this SID, a capability SID, or ALL_APPLICATION_PACKAGES. |
| `confinement_capabilities` | SID_AND_ATTRIBUTES[] | Declared access capabilities for confined processes. Empty if none. The `attributes` field is carried for wire-format uniformity only; AccessCheck treats capability membership as presence-based and does not consult `SE_GROUP_ENABLED` or `SE_GROUP_USE_FOR_DENY_ONLY` for confinement SID matching. |
| `isolation_boundary` | bool | Enables namespace filtering on top of confinement. Objects outside the boundary are invisible, not just denied. Requires `confinement_sid`. Settable at creation; not enforced in v0.20. |
| `confinement_exempt` | bool | Escape hatch. Confinement restrictions are not evaluated. |

## Audit (adjustable)

| Field | Type | Description |
|---|---|---|
| `audit_policy` | u32 | Per-token audit overrides, encoded as a bitmask. Fixed at creation time — no adjustment ioctl exists. Additive — forces audit events that system-wide policy would not generate, but MUST NOT suppress events that system-wide policy requires. |

Audit policy flags:

| Flag | Value | Description |
|------|-------|-------------|
| OBJECT_ACCESS_SUCCESS | 0x0001 | Audit successful object access operations. |
| OBJECT_ACCESS_FAILURE | 0x0002 | Audit failed object access operations. |
| PRIVILEGE_USE_SUCCESS | 0x0004 | Audit successful privilege exercises: the privilege contributed requested bits that survive to the final granted result. |
| PRIVILEGE_USE_FAILURE | 0x0008 | Audit failed privilege exercises: the privilege contributed requested bits during evaluation, but those bits do not survive to the final granted result. |

Follows impersonation: if service A impersonates client B and client B's token has auditing enabled for a category, operations during impersonation are audited under client B's identity. Default value at creation: 0 (no per-token audit overrides).

## Credential projection (fixed)

| Field | Description |
|---|---|
| `projected_uid` | Pre-computed Linux UID from the user SID's directory `uidNumber` attribute. 65534 if unmapped. |
| `projected_gid` | Pre-computed Linux primary GID. 65534 if unmapped. |
| `projected_supplementary_gids` | Pre-computed Linux supplementary GIDs from group SIDs where `gidNumber` attributes exist. |

Computed by authd at token creation time, stored on the token. KACS MUST NOT resolve SID-to-UID mappings at runtime. Projection reflects all groups regardless of enabled/disabled state — AdjustGroups MUST NOT trigger projection recalculation.

## Token security (adjustable)

| Field | Description |
|---|---|
| `security_descriptor` | The token's own SD. Controls who can query, adjust, duplicate, or impersonate this token. |

## Internal

| Field | Description |
|---|---|
| `refcount` | Reference count. Token is freed when the last reference drops. Not exposed to userspace. |
