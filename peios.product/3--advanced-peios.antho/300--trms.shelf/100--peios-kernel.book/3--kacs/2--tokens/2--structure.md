---
title: Token Structure
description: Every token field by mutability class — fixed identity, adjustable privileges, one-way elevation — and what each carries.
---

Token fields fall into three mutability classes. **Fixed** fields are
set at creation and never change — every security-critical identity
field is fixed. **Adjustable** fields can be modified at runtime
through the adjustment operations (§3.2.5). **One-way** fields can be
set or tightened but never cleared or loosened.

## Identity core (fixed)

| Field | Type | Description |
|---|---|---|
| `user_sid` | SID | The token's primary identity. |
| `user_deny_only` | bool | When true, the user SID matches only deny ACEs, never allow ACEs. Set at creation by CreateToken or FilterToken. True whenever `write_restricted` is true. |
| `groups` | SID_AND_ATTRIBUTES[] | Group memberships. The set of SIDs is fixed at creation; the per-group attribute flags are adjustable. |
| `restricted_sids` | SID_AND_ATTRIBUTES[]? | Secondary SID list for restricted tokens, null on unrestricted ones. Set at creation by CreateToken or FilterToken. AccessCheck treats the list as presence-based: a restricting SID participates whenever it is present, and neither `SE_GROUP_ENABLED` nor `SE_GROUP_USE_FOR_DENY_ONLY` affects restricted-pass matching. |
| `write_restricted` | bool | When true, the restricted SID check applies only to write access. Set at creation by CreateToken or FilterToken. |

The **logon SID** — `S-1-5-5-X-Y`, tying the token to its
LogonSession — is not stored as a token field at all. It is derived
from the session on every read, and materialised once in `groups`
carrying `SE_GROUP_LOGON_ID`, which is where AccessCheck finds it.

The group SID set is fixed at creation — adjustment never adds or
removes a SID. Individual groups can be enabled or disabled by
modifying `SE_GROUP_ENABLED`, within two limits: a mandatory group
(`SE_GROUP_MANDATORY`) cannot be disabled, and a deny-only group
(`SE_GROUP_USE_FOR_DENY_ONLY`) cannot be re-enabled.

A token holds at most 1024 group entries including the kernel-injected
logon SID, so CreateToken accepts at most 1023 caller-supplied groups.

## Token type (fixed)

| Field | Type | Description |
|---|---|---|
| `token_type` | enum | Primary or Impersonation. |
| `impersonation_level` | enum | Anonymous, Identification, Impersonation, or Delegation. On every token it is the ceiling on what may be derived from it: an impersonation token acts at this level, and a primary token bounds everything captured from, conveyed by, or duplicated out of the process carrying it (§3.5.1). |

## Integrity (fixed)

| Field | Type | Description |
|---|---|---|
| `integrity_level` | uint | Numeric integrity level. Standard values are 0 (Untrusted), 4096 (Low), 8192 (Medium), 12288 (High), 16384 (System), but any unsigned integer is valid and is compared numerically against object labels. |
| `mandatory_policy` | flags | `NO_WRITE_UP` (0x0001) and `NEW_PROCESS_MIN` (0x0002). Per-token MIC enforcement policy, set at creation. |

`mandatory_policy` is immutable: a process cannot change its own MIC
constraints at runtime, neither loosening nor tightening them. This is
a deliberate departure from MS-DTYP, where the mandatory policy is
runtime-modifiable — which reduces MIC to a constraint that stops only
processes not actively trying to bypass it. Immutability is what makes
MIC a real boundary here, and it is also what allows the impersonation
integrity ceiling (§3.5) to be enforced unconditionally.

## Privileges (adjustable)

Each privilege on a token has four independent states.

**Present** — the privilege exists on the token. A present privilege
can be removed permanently, but no privilege can be added after
creation. **Enabled** — the privilege is currently active; only
present privileges can be enabled or disabled. **Enabled by default**
— the creation-time enabled state, which adjustment can restore.
**Used** — the privilege has been exercised during this token's
lifetime; monotonic, and never cleared once set.

The lifecycle runs: present and disabled, to enabled, to used, then
optionally disabled, then optionally removed permanently. Removal
clears the privilege from the present, enabled, and enabled-by-default
states together.

The four states are encoded as four 64-bit bitmasks, one bit per
defined privilege, which makes a privilege check constant-time and a
multi-privilege operation atomic.

## Elevation (one-way)

| Field | Type | Description |
|---|---|---|
| `elevation_type` | enum | Default (non-elevated), Full (elevated), or Limited (filtered). |

A token is created as Default. Only `KACS_IOC_LINK_TOKENS` sets Full
or Limited, when a linked pair is established, and once set neither
reverts to Default on that token object. The role is sticky: relinking
can replace the partner but never converts Full to Limited or the
reverse. DuplicateToken and FilterToken produce new token objects
whose `elevation_type` starts again at Default, because a new token is
not part of any linked pair.

Linked pairs are associated at the LogonSession level rather than
stored on individual tokens; §3.2.6 describes the pairing mechanism.

## Default object security (adjustable)

| Field | Description |
|---|---|
| `owner_sid_index` | Index into `[user_sid, groups...]` selecting the default owner SID for new objects: 0 is the user SID, 1..N are `groups[0..N-1]`. The referenced SID is the user SID or a group carrying `SE_GROUP_OWNER`. |
| `primary_group_index` | Index into `[user_sid, groups...]` selecting the default primary group. The referenced SID is the user SID or any group SID on the token. |
| `default_dacl` | The DACL applied to objects this token creates when no explicit descriptor is supplied. |

Storing indices rather than SID copies keeps the owner and primary
group consistent with the group array they name.

## Metadata (fixed)

| Field | Type | Description |
|---|---|---|
| `token_id` | LUID | Unique identifier for this token instance. |
| `token_guid` | UUID | 128-bit identifier for this token instance, generated by the kernel at creation and immutable. Used by KMES and other kernel-internal consumers for identity stamping and event correlation. |
| `auth_id` | LUID | The LogonSession LUID, linking the token to the authentication event that produced it. |
| `source` | TOKEN_SOURCE | Who minted the token: an 8-character name plus a LUID. |
| `created_at` | timestamp | When the original token was minted by CreateToken. Copied unchanged by DuplicateToken, FilterToken, and `NEW_PROCESS_MIN`, so it tracks original minting rather than duplication. |
| `expiration` | timestamp | When the token becomes invalid; zero means no expiry. Not enforced by AccessCheck. |
| `origin` | LUID | The originating LogonSession for derived tokens, such as S4U or network logon. |

## Mutation tracking (adjustable)

| Field | Description |
|---|---|
| `modified_id` | Counter incremented on any token adjustment. |

Marking a privilege used is audit and accounting state rather than an
access-decision input, so it stays monotonic but does not bump
`modified_id`. Setting the elevation type is the one other mutation
that leaves the counter alone.

The counter is intended as a cache invalidation key — a `modified_id`
that has changed since a cached decision was taken means the decision
is stale. Nothing currently reads it for that purpose: it is
maintained on every adjustment and reported through the statistics
query class, and no cache anywhere invalidates on it.

## Interactivity scope (adjustable)

| Field | Description |
|---|---|
| `interactivity_scope` | 0 for services, which have no interactive environment; 1 and above for interactive and remote user environments. Changing it requires `SeTcbPrivilege`. |

## Claims and security attributes (fixed)

| Field | Type | Description |
|---|---|---|
| `user_claims` | CLAIM_ATTRIBUTES[] | Name-value pairs from the user's directory object, fed into conditional ACE evaluation. |
| `device_claims` | CLAIM_ATTRIBUTES[] | Name-value pairs from the machine's directory object. |

## LCS registry credentials (fixed)

| Field | Type | Description |
|---|---|---|
| `lcs_scope_guids` | GUID[] | Ordered private registry scope GUIDs used by LCS private hive routing. LCS checks the list in order before falling back to global hives. |
| `lcs_private_layers` | string[] | Registry layer names visible to this token even when disabled globally, using LCS layer-name syntax and matching rules. |

These are KACS-owned credential material belonging to LCS. They are
fixed at creation and copied by duplication and filtering, and
attaching them is authorized by the same trusted-minting gate as the
rest of CreateToken — only a caller holding `SeCreateTokenPrivilege`
can create a token carrying them.

## Device identity (fixed)

| Field | Type | Description |
|---|---|---|
| `device_groups` | SID_AND_ATTRIBUTES[]? | The machine's group memberships, for compound identity. |
| `restricted_device_groups` | SID_AND_ATTRIBUTES[]? | Filtered device groups for restricted tokens. |

## Confinement (fixed)

| Field | Type | Description |
|---|---|---|
| `confinement_sid` | SID? | Places the token in a default-deny sandbox; null means unconfined. When set, AccessCheck switches to default-deny and access requires an explicit grant to this SID or to a SID present in `confinement_capabilities`. |
| `confinement_capabilities` | SID_AND_ATTRIBUTES[] | Declared access capabilities for a confined process, empty if none. The `attributes` field is carried for wire-format uniformity only: AccessCheck treats capability membership as presence-based and consults neither `SE_GROUP_ENABLED` nor `SE_GROUP_USE_FOR_DENY_ONLY` when matching confinement SIDs. |
| `isolation_boundary` | bool | Adds namespace filtering on top of confinement, making objects outside the boundary invisible rather than merely denied. Requires `confinement_sid`. Settable at creation but not enforced. |
| `confinement_exempt` | bool | Escape hatch: confinement restrictions are not evaluated at all. |

`ALL_APPLICATION_PACKAGES` participates only when it is present in
`confinement_capabilities`. KACS never synthesises it, and equally
never rejects an otherwise valid confined token merely because it is
present — strict confinement is expressed by the caller omitting it.
Deciding which capabilities a package token receives is authd's job
and policy tooling's, not the kernel's.

## Audit (fixed)

| Field | Type | Description |
|---|---|---|
| `audit_policy` | u32 | Per-token audit overrides as a bitmask, fixed at creation — no adjustment operation exists. |

| Flag | Value | Description |
|---|---|---|
| `OBJECT_ACCESS_SUCCESS` | 0x0001 | Audit successful object access. |
| `OBJECT_ACCESS_FAILURE` | 0x0002 | Audit failed object access. |
| `PRIVILEGE_USE_SUCCESS` | 0x0004 | Audit successful privilege exercises: the privilege contributed requested bits that survive into the final granted result. |
| `PRIVILEGE_USE_FAILURE` | 0x0008 | Audit failed privilege exercises: the privilege contributed requested bits during evaluation, but they do not survive into the final result. |

The policy is additive. It forces audit events that system-wide policy
would not generate, and cannot suppress events that system-wide policy
requires. It follows impersonation: when service A impersonates client
B and B's token has a category enabled, operations during
impersonation are audited under B's identity. The creation default is
0.

## Credential projection (fixed)

| Field | Description |
|---|---|
| `projected_uid` | Linux UID for the user SID, precomputed by authd when the token is minted (PSPU §2); 65534 for the anonymous identity. |
| `projected_gid` | Linux primary GID, precomputed the same way; 65534 for the anonymous identity. |
| `projected_supplementary_gids` | Linux supplementary GIDs, one per group SID, precomputed the same way. |

authd computes these at token creation and they are stored on the
token; KACS never resolves a SID-to-UID mapping at runtime. Projection
reflects all groups regardless of enabled state, so adjusting groups
does not trigger recalculation. §3.10 covers how the projection is
used.

## Token security (adjustable)

| Field | Description |
|---|---|
| `security_descriptor` | The token's own SD, controlling who may query, adjust, duplicate, or impersonate it. |

## Internal

| Field | Description |
|---|---|
| `refcount` | Reference count; the token is freed when the last reference drops. Not exposed to userspace. |
