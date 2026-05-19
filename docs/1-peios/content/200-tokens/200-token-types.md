---
title: Token types and fields
type: concept
description: Tokens are classified along several orthogonal axes — primary vs impersonation, impersonation level, restricted or not, elevation pair. This page covers each axis and walks through the token's fields grouped by purpose.
related:
  - peios/tokens/overview
  - peios/tokens/lifecycle
  - peios/tokens/restricted-tokens
  - peios/tokens/elevation
  - peios/impersonation/overview
---

Every token in Peios is classified along several axes at once. A given token is either a primary token or an impersonation token. If it is an impersonation token it has an impersonation level. It is either restricted or not. If it is part of an elevation pair it has an elevation type. These are not types in an inheritance sense — they are independent dials, and a token's behaviour is the product of all of them.

This page walks through each axis, then through the token's fields grouped by what they do.

## token_type — primary or impersonation

The first and most important classification.

A **primary token** is the baseline identity of a process. Every process has exactly one. It is inherited across fork — child processes start with a copy of the parent's primary token — and survives exec. When a thread runs without doing anything special, AccessCheck reads its primary token.

An **impersonation token** is a thread-local override. A thread installs an impersonation token to act as someone else for a span of time, then reverts back to its primary. While the impersonation is in effect, AccessCheck reads the impersonation token instead of the primary. Other threads in the same process are unaffected.

The two types are not interchangeable. Trying to install a primary token as a thread's impersonation, or vice versa, fails. The kernel's `kacs_open_self_token` and related syscalls return tokens of the correct type for what they were asked to do.

| Use case | Token type |
|---|---|
| A login session's identity | Primary |
| A server thread acting on behalf of a connected client | Impersonation |
| A service running with the identity authd assigned to it | Primary |
| A thread querying its caller's identity for an audit log entry | Impersonation (at the Identification level — see below) |

## impersonation_level — how far an identity may travel

Every token carries an impersonation level. For primary tokens this is set to a conventional value (Anonymous) and ignored. For impersonation tokens it is what bounds what the impersonator may do.

There are four levels, ordered from least to most permissive:

| Level | What a server may do with this token |
|---|---|
| **Anonymous** | No identity. The token's user SID is the well-known Anonymous SID (`S-1-5-7`). The server learns nothing about the client. |
| **Identification** | The server may *inspect* the client's identity — read their SIDs, groups, integrity level — but may not *use* the token for any access check. AccessCheck with an Identification-level token returns ACCESS_DENIED immediately, no matter what. |
| **Impersonation** | The server may act as the client for all local operations. This is the default, and the level most server-to-client code paths assume. |
| **Delegation** | Same as Impersonation locally, plus the server may forward the client's credentials to a remote machine over Kerberos. KACS only tracks the level; the actual forwarding is authd's job. |

The level is set by the **client**, on the socket, before connecting. The server cannot raise it. It can only end up with the level the client granted, or lower if other constraints intervene (see [Impersonation](~peios/impersonation/overview) for the full two-gate model).

The Identification level deserves a flag. A common bug — in services not written for Peios — is to take a client's token and try to open files as them, finding that every open returns ACCESS_DENIED for reasons the code cannot diagnose. The cause is almost always that the client connected at Identification level and the server is supposed to be inspecting, not acting. The correct fix is at the client end: ask for Impersonation.

## restricted — a secondary identity check

A **restricted token** carries two SID lists: the normal `groups` list and a secondary `restricted_sids` list. During AccessCheck the kernel runs the DACL walk twice and intersects the results — once with the full identity, once with only the restricted SIDs. A right is granted only if both passes grant it.

The effect is to limit a token's identity-based access to what the restricted SIDs would independently receive. The user is still the same user; they just cannot use group memberships or other SIDs that are not in the restricted list to satisfy an ACE.

A **write-restricted** token is the same idea, but the intersection applies only to write-category rights. Reads and execute come from the normal pass alone. This is the common case: a sandbox that should be able to read system files but only write into a narrow allowed set.

Both variants are covered in detail under [Restricted and write-restricted tokens](~peios/tokens/restricted-tokens). For this page it is enough to know that "restricted" is a property of the token, set at creation by FilterToken, and that the kernel handles the second pass automatically.

## elevation_type — half of a linked pair

When a principal has both a normal (Limited) token and an elevated (Full) token — the UAC-style pattern — the two tokens are linked at the session level. Each carries an `elevation_type` saying which half it is:

| Value | Meaning |
|---|---|
| **Default** | The token is not part of a linked pair. Most tokens. |
| **Full** | The elevated half of a linked pair. |
| **Limited** | The non-elevated half of a linked pair. |

A linked pair is established by an explicit call to `KACS_IOC_LINK_TOKENS`. The elevation type does not change anything about the token's access rights by itself — it is a label that lets the system locate the partner token when the user requests elevation. The mechanics live in [Elevation and linked tokens](~peios/tokens/elevation).

## Field mutability classes

Token fields fall into three classes. Knowing which class a field is in tells you whether you can ever change it after the token is minted.

| Class | Meaning | Examples |
|---|---|---|
| **Fixed** | Set at creation, never changes. Cannot be adjusted at runtime even by SYSTEM. | `user_sid`, `groups[].sid`, `logon_sid`, `restricted_sids`, `token_id`, `auth_id`, `created_at`, `source`, `confinement_sid`, `mandatory_policy`. |
| **Adjustable** | Can be changed at runtime through a specific syscall. | Privilege enabled-state (via AdjustPrivileges), group enabled-state (via AdjustGroups), default DACL / owner index / primary group index (via AdjustDefault), `security_descriptor` (via kacs_set_sd). |
| **One-way** | Can be tightened but never loosened. | Privilege presence (a privilege can be removed but not re-added), group `USE_FOR_DENY_ONLY` (can be set but not cleared). |

This split is the source of one rule worth memorising: **the identity in a token cannot change**. You cannot relabel a token to a different user. You cannot add a group to a token. You can only adjust how existing identity bits are *used* — enable or disable a privilege, mark a group as deny-only, narrow the default DACL.

If you need a different identity, you need a different token. Either authd mints a new one for you (with a re-authentication), or you DuplicateToken / FilterToken your existing one into a more restricted copy.

## Fields by purpose

The rest of this page walks through the token's fields grouped by what they do. None of this is a low-level binary layout — that lives in the [Kernel ABI reference](~peios/kernel-abi-reference/overview) topic. This is the conceptual field list.

### Identity

The fields that say who the token represents.

| Field | What it is |
|---|---|
| `user_sid` | The primary identity of the token. The principal's SID. |
| `groups` | An array of `SID_AND_ATTRIBUTES` — every group the principal is a member of, each with its current enabled/disabled state and other flags. |
| `logon_sid` | The session-specific SID (`S-1-5-5-X-Y`) for the logon session this token belongs to. Also appears in `groups` with the `SE_GROUP_LOGON_ID` flag. |
| `restricted_sids` | Secondary identity list for restricted tokens. Empty on unrestricted tokens. |

### Type and level

| Field | What it is |
|---|---|
| `token_type` | Primary or Impersonation. |
| `impersonation_level` | One of the four levels listed above (only meaningful for Impersonation tokens). |
| `integrity_level` | One of Untrusted / Low / Medium / High / System. |
| `mandatory_policy` | The token's MIC enforcement flags (`NO_WRITE_UP`, `NEW_PROCESS_MIN`). |

### Defaults

These fields contribute to the security descriptor of a new object when the creator does not supply one explicitly.

| Field | What it is |
|---|---|
| `owner_sid_index` | Index into `[user_sid, groups[0..N-1]]` selecting which SID becomes the default owner. |
| `primary_group_index` | Same idea for the default primary group. |
| `default_dacl` | The DACL applied to new objects when no explicit SD is supplied. |

### Session and provenance

| Field | What it is |
|---|---|
| `token_id` | A unique LUID identifying this token instance. |
| `auth_id` | The LUID of the logon session this token belongs to. |
| `source` | An 8-character name plus a LUID identifying the component that minted the token (e.g. authd). |
| `created_at` | Timestamp of original minting. Copied unchanged by DuplicateToken and FilterToken. |
| `expiration` | Expiry timestamp. Set by authd. **Informational only in v0.20** — not enforced by AccessCheck. |
| `origin` | The originating logon session for derived tokens (S4U, network logon). |
| `modified_id` | A counter bumped on every adjustment. Used as a cache-invalidation key. |

### Privileges

Privileges live in a 64-bit bitmask with four states per privilege:

- **Absent** — not on this token at all.
- **Present, disabled** — on the token but not currently in effect. May be enabled.
- **Present, enabled** — in effect; AccessCheck will use it.
- **Used** — a sticky audit bit set when the privilege has been exercised. Never cleared.

See [Privileges](~peios/privileges/overview) for the model in detail and the catalog of named privileges.

### Confinement

| Field | What it is |
|---|---|
| `confinement_sid` | If non-null, the token is for a confined application; its identity for access checks is intersected with this SID. |
| `confinement_capabilities` | The list of capability SIDs the confined application has declared. |
| `confinement_exempt` | Escape hatch — if set, confinement is skipped entirely. |
| `isolation_boundary` | Reserved for future use; not enforced in v0.20. |

See [Confinement](~peios/confinement/overview) for the sandbox model.

### Claims

| Field | What it is |
|---|---|
| `user_claims` | Typed attributes about the user, populated from the directory at authentication time. Used by `@User.*` references in conditional ACEs. |
| `device_claims` | Same idea for the machine. Used by `@Device.*`. |
| `device_groups` | The machine's group memberships, for compound identity. |

See [Claims on a token](~peios/identity/claims).

### Projection

These fields hold pre-computed Linux UID/GID values for compatibility. They are derived from the token, never the other way around.

| Field | What it is |
|---|---|
| `projected_uid` | The Linux UID the token's identity maps to (or `65534` if unmapped). |
| `projected_gid` | Same for primary GID. |
| `projected_supplementary_gids` | Same for supplementary GIDs. |

See [Linux compatibility](~peios/linux-compatibility/overview) for what consumes these.

### Audit policy

| Field | What it is |
|---|---|
| `audit_policy` | A bitmask of per-token forced-audit flags (`OBJECT_ACCESS_SUCCESS`, `OBJECT_ACCESS_FAILURE`, `PRIVILEGE_USE_SUCCESS`, `PRIVILEGE_USE_FAILURE`). |

When a flag is set, AccessCheck emits the corresponding audit event regardless of the object's SACL.

### Self SD

| Field | What it is |
|---|---|
| `security_descriptor` | The token is itself a protected object; this is its own SD. Governs who may query, duplicate, impersonate, install, or adjust the token. |

### Other

| Field | What it is |
|---|---|
| `interactive_session_id` | The interactive session number. Zero for services. Adjustable only with `SeTcbPrivilege`. |
| `elevation_type` | Default / Full / Limited, for linked-pair membership. |
