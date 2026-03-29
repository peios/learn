---
title: Token Structure
order: 2
---

A token carries identity, policy, and metadata fields. Fields are organized by concern and annotated with mutability:

- **Fixed** — set at creation, never changes. The security-critical identity fields fall into this category.
- **Adjustable** — may be modified at runtime via the adjustment operations defined in this specification.
- **One-way** — can be set or tightened but never cleared or loosened.

## Identity core (fixed)

| Field | Type | Description |
|---|---|---|
| `user_sid` | SID | The token's primary identity. |
| `user_deny_only` | bool | If true, the user SID matches only deny ACEs, not allow ACEs. Set by FilterToken when creating a write-restricted token. |
| `groups` | SID_AND_ATTRIBUTES[] | Group memberships. The set of SIDs is fixed at creation; per-group attribute flags are adjustable (see below). |
| `logon_sid` | SID | Per-authentication-event SID (`S-1-5-5-X-Y`). Ties the token to its logon session. |
| `restricted_sids` | SID_AND_ATTRIBUTES[]? | Secondary SID list for restricted tokens. Null on unrestricted tokens. Set by FilterToken at creation. |
| `write_restricted` | bool | If true, the restricted SID check applies only to write access. Set by FilterToken at creation. |

The set of group SIDs on a token is fixed at creation — AdjustGroups MUST NOT add or remove SIDs. However, individual groups MAY be enabled or disabled by modifying SE_GROUP_ENABLED, subject to constraints: mandatory groups (SE_GROUP_MANDATORY) MUST NOT be disabled, and deny-only groups (SE_GROUP_USE_FOR_DENY_ONLY) MUST NOT be re-enabled.

## Token type (fixed)

| Field | Type | Description |
|---|---|---|
| `token_type` | enum | Primary or Impersonation. |
| `impersonation_level` | enum | Anonymous, Identification, Impersonation, or Delegation. Meaningful only on impersonation tokens. |

## Integrity (fixed)

| Field | Type | Description |
|---|---|---|
| `integrity_level` | enum | Untrusted, Low, Medium, High, or System. |
| `mandatory_policy` | flags | NO_WRITE_UP, NEW_PROCESS_MIN. Per-token MIC enforcement policy. Set at creation time. |

The `mandatory_policy` field is fixed. A process MUST NOT loosen its own MIC constraints at runtime.

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

## Elevation (fixed)

| Field | Type | Description |
|---|---|---|
| `elevation_type` | enum | Default (non-elevated), Full (elevated), or Limited (filtered). |

Linked token pairs are associated at the session level, not stored on individual tokens. See the Linked Tokens and Elevation section for the pairing mechanism.

## Default object security (adjustable)

| Field | Description |
|---|---|
| `owner_sid` | The SID used as the default owner for new objects. MUST reference the user SID or a group on the token with SE_GROUP_OWNER. |
| `primary_group_sid` | The SID used as the default primary group for new objects. MUST reference the user SID or a group SID on the token. |
| `default_dacl` | DACL applied to objects created by this token when no explicit SD is provided. |

> [!INFORMATIVE]
> An implementation MAY store the owner and primary group as indices into the token's SID arrays rather than as separate SID copies.

## Metadata (fixed)

| Field | Type | Description |
|---|---|---|
| `token_id` | LUID | Unique identifier for this token instance. |
| `auth_id` | LUID | Logon session LUID. Links to the authentication event that produced this token. |
| `source` | TOKEN_SOURCE | Who minted this token. 8-character name + LUID. |
| `created_at` | timestamp | When the token was created. |
| `expiration` | timestamp | When the token becomes invalid. Zero = no expiry. Not enforced by AccessCheck in v0.20. |
| `origin` | LUID | Originating logon session for derived tokens (S4U, network logon). |

## Mutation tracking (adjustable)

| Field | Description |
|---|---|
| `modified_id` | Counter incremented on any token adjustment. Serves as a cache invalidation key — if `modified_id` has changed since the last AccessCheck, cached decisions are stale. |

## Session (adjustable)

| Field | Description |
|---|---|
| `interactive_session_id` | Interactive session number. 0 for services, 1+ for interactive/remote. Changing this field requires `SeTcbPrivilege`. |

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
| `confinement_capabilities` | SID_AND_ATTRIBUTES[] | Declared access capabilities for confined processes. Empty if none. |
| `isolation_boundary` | bool | Enables namespace filtering on top of confinement. Objects outside the boundary are invisible, not just denied. Requires `confinement_sid`. |
| `confinement_exempt` | bool | Escape hatch. Confinement restrictions are not evaluated. |

## Audit (adjustable)

| Field | Description |
|---|---|
| `audit_policy` | Per-token audit overrides, organized by audit category. Additive — forces audit events that system-wide policy would not generate, but MUST NOT suppress events that system-wide policy requires. Follows impersonation: if service A impersonates client B and client B's token has auditing enabled for a category, operations during impersonation are audited under client B's identity. |

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
