---
title: Token Creation
description: The three operations that produce a token — CreateToken from nothing, DuplicateToken from another, FilterToken for a restricted one.
---

Three operations create tokens, each for a different purpose:
CreateToken mints one from nothing, DuplicateToken copies one, and
FilterToken produces a strictly weaker copy.

## CreateToken

Mints a new token from scratch. The caller supplies the
security-meaningful content; the kernel generates the internal
bookkeeping and validates the structural invariants. The operation is
gated by `SeCreateTokenPrivilege`.

The caller supplies `user_sid`, `groups` with their attributes,
privileges as `privs_present` plus `privs_enabled`, `owner_sid_index`,
`primary_group_index`, `default_dacl`, `integrity_level`,
`mandatory_policy`, `token_type`, `impersonation_level`, `auth_id`
referencing an existing LogonSession, `expiration` (0 for none),
`audit_policy`, `source` as a name plus LUID, `user_claims`,
`device_claims`, `lcs_scope_guids`, `lcs_private_layers`,
`device_groups`, `restricted_sids`, `restricted_device_groups`,
`confinement_sid`, `confinement_capabilities`, `confinement_exempt`,
`isolation_boundary`, `write_restricted`, `user_deny_only`,
`projected_uid`, `projected_gid`, `projected_supplementary_gids`,
`origin`, and `interactivity_scope`. The wire format is in §3.A.

Including the well-known implicit groups is the caller's
responsibility — Everyone (`S-1-1-0`), Authenticated Users
(`S-1-5-11`), and whatever else the principal's authentication context
implies, such as `S-1-5-4` Interactive, `S-1-5-6` Service, or
`S-1-5-15` This Organization. The kernel injects none of these. The
logon SID is the sole kernel-generated group.

The kernel generates `token_id` as a LUID, `token_guid`, `modified_id`
initialised to `token_id`, `created_at` as the current time,
`elevation_type` always Default, the token's own default security
descriptor (§3.2.7), and `logon_sid`, derived from the LogonSession ID
as `S-1-5-5-{id >> 32}-{id & 0xFFFFFFFF}`.

The logon SID is injected into the groups array carrying
`SE_GROUP_MANDATORY | SE_GROUP_ENABLED_BY_DEFAULT | SE_GROUP_ENABLED |
SE_GROUP_LOGON_ID`, appended after the caller's groups. Callers do not
include it themselves. Because the injected entry is appended,
`owner_sid_index` and `primary_group_index` are interpreted relative
to the caller-supplied groups — 0 for the user SID, 1..N for the
caller's groups — and not against the array with the logon SID in it.

Validation covers, in turn: that the caller holds
`SeCreateTokenPrivilege`; that every SID is structurally well-formed;
that the owner SID is the user SID or a group carrying
`SE_GROUP_OWNER`, resolved to `owner_sid_index`; that the primary
group SID is the user SID or a group on the token, resolved to
`primary_group_index`; that `auth_id` references an existing
LogonSession; that a Primary token carries impersonation level
Impersonation or Delegation (see below); that `user_deny_only` is
true whenever `write_restricted`
is; that `confinement_sid` is present whenever `isolation_boundary`
is; that the wire format's `elevation_type` field is 0, since the
kernel always sets Default itself; and that the caller's group count
plus the injected logon SID fits the 1024-entry limit.

The optional LCS registry credential extension, when present, has to
use the version and layout of §3.A, and carries at most 256 scope
GUIDs and at most 256 private layer names, with no nil scope GUID, no
duplicate scope GUIDs, no empty or overlong layer names, and no
duplicate layer names under LCS case-insensitive matching. Malformed
LCS credentials fail the whole call closed.

The impersonation level on a primary is the ceiling for everything
derived from it (§3.5.1), so a minter chooses it deliberately: authd
mints logon tokens at Delegation and lets each client lower the level
per connection. A primary at Identification or Anonymous — one that
peers could identify but never act as, or not identify at all — is a
coherent shape the ratchet permits in principle, but CreateToken
currently refuses it: every minter used to pass a conventional
Anonymous that the kernel ignored, and accepting it would turn an
un-migrated minter into a source of identities nobody can impersonate.
The restriction is a migration guard, not a property of the model.

The kernel does not authenticate the user, look up SIDs in the
directory, resolve SID-to-UID mappings, or check that the principal
exists at all. Holding `SeCreateTokenPrivilege` is what makes the
caller trusted, and that trust is total.

The call returns a token file descriptor. Since CreateToken takes no
desired-access parameter, the returned handle always carries a cached
access mask of `TOKEN_ALL_ACCESS`.

## DuplicateToken

Creates an independent copy of an existing token, requiring
`TOKEN_DUPLICATE` access on the source.

Two things may change during duplication. The **token type** may go
from primary to impersonation or the reverse. The **impersonation
level** is chosen by the caller and is a ratchet: whatever the types
involved, the new level has to be equal to or lower than the source's,
and asking for more fails with `EINVAL`. A primary minted at
Delegation can be duplicated to an impersonation token at any level; a
primary at Impersonation cannot yield a Delegation-level token; an
Identification-level token cannot be duplicated up to Impersonation or
Delegation. The level only ever goes down — reaching a higher one
again means minting a fresh token with CreateToken.

Duplicating **to Primary** is how an impersonated identity becomes a
process — the server's impersonation token, converted, is what a
service manager installs on a child it launches as that client. The
result keeps the identity and the level, so a primary made from a
client captured at Impersonation is itself capped at Impersonation and
so is every process and token descended from it. The kernel refuses a
Primary result below Impersonation: an Identification-level token
cannot pass AccessCheck and Anonymous is the singleton identity, so a
process could never be either.

On the new token, `token_id` and `token_guid` are fresh, `modified_id`
is initialised to the new `token_id`, and `elevation_type` resets to
Default because the copy belongs to no linked pair. `token_type` and
`impersonation_level` are as the caller specified, within the rules
above. The token's own descriptor is a fresh default (§3.2.7): no
custom descriptor can be supplied at duplication time, and changing it
afterwards means using `WRITE_DAC` on the new handle.

Everything else is copied from the source: `user_sid`,
`user_deny_only`, `logon_sid`; `groups` with all per-group attributes;
`restricted_sids` and `write_restricted`; the privilege present,
enabled, enabled-by-default **and used** states; `integrity_level` and
`mandatory_policy`; `auth_id`, `origin`, `source`, `created_at`,
`expiration`, `audit_policy`; `interactivity_scope`; `default_dacl`,
`owner_sid_index`, `primary_group_index`; `user_claims`,
`device_claims`, `device_groups`, `restricted_device_groups`;
`lcs_scope_guids` and `lcs_private_layers`; `confinement_sid`,
`confinement_capabilities`, `confinement_exempt`; and the three
projection fields.

One target is not a copy at all. Duplicating to **Impersonation at
Anonymous level** discards the source entirely and returns a fresh
token of the boot Anonymous shape — user SID `S-1-5-7`, Everyone as
its only group, no privileges, Untrusted integrity, and LogonSession
998 rather than the source's. None of the copied-field rules above
apply to it. Assuming Anonymous is an identity boundary rather than a
level change, so the operation constructs the minimal identity instead
of narrowing the caller's.

The original token is unaffected.

## FilterToken

Creates a restricted copy, requiring `TOKEN_DUPLICATE` access on the
source. Filtering only ever weakens: there is no parameter that grants
anything.

It can **remove privileges**, deleting them permanently from the new
token by clearing them from the present, enabled, and
enabled-by-default states at once. It can **set groups to deny-only**,
giving them `SE_GROUP_USE_FOR_DENY_ONLY` so they block access through
deny ACEs but never grant it through allow ACEs — permanently, with no
way back. It can **add restricted SIDs**, a secondary list that makes
AccessCheck evaluate the DACL twice, granting access only when the
normal SIDs and the restricted SIDs independently both pass. And it
can **enable write-restricted mode**, limiting that second evaluation
to write operations so reads use the normal list alone; enabling it
forces `user_deny_only` true on the new token.

Input validation is all-or-nothing — a single malformed entry means no
token is created. The deny-only list uses zero-based group indices
into the source's group array, and a duplicate or out-of-range index
is invalid. The restricting SID blob has to parse exactly as the
declared packed SID list, with no truncated or trailing bytes. If the
source token is already restricted and the intersection of its
restricted SID list with the supplied list is empty, the request is
invalid and nothing is created.

On the new token, `token_id` and `token_guid` are fresh, `modified_id`
is initialised to the new `token_id`, and `elevation_type` resets to
Default. The privilege states are the source's modified by the removal
list, except that **`used` resets to 0** — unlike duplication, which
carries it across. `groups` keeps the source's SIDs with attributes
modified per the deny-only list, adding and removing nothing.
`restricted_sids` is the supplied list, or its intersection with the
source's when the source was already restricted. `write_restricted` is
sticky: set if requested or if the source had it. `user_deny_only` is
true when write-restricted is enabled and otherwise copied.
`user_sid`, `logon_sid`, `integrity_level`, `mandatory_policy`,
`token_type` and `impersonation_level` are copied, as are `auth_id`,
`origin`, `source`, `created_at`, `expiration`, `audit_policy`,
`default_dacl`, `owner_sid_index`, `primary_group_index`, the claims
and device group arrays, the LCS credentials, the confinement fields,
and the projection fields. The token's descriptor is a fresh default.
