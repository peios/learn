---
title: User and Group Records
---

This section defines the fields of the user and group records. Storage
encoding is §3.5; the credential portion of the user record is §3.3.

## The user record

A user record is a superset of the source-provided columns of the
resolved principal (§4); it adds the material that does not cross the
seam (credentials and raw memberships) and bookkeeping.

| Field | Meaning |
|---|---|
| `rid` | RID; the user SID is `machine_sid` + `rid` |
| `object_guid` | Stable 16-byte identity (UUIDv4 from a CSPRNG — §9), independent of name and RID; makes rename safe |
| `sam_account_name` | Login name; unique; matched case-insensitively (folded form per §3.5) |
| `display_name` | Human-readable name |
| `upn` | Optional user principal name (meaningful once domain-capable) |
| `account_flags` | Account-control flags (disabled, password-never-expires, password-not-required, smartcard-required, service-account, …). A **service-account** record is a purpose-made service principal (§5.4): non-interactive, holds no credential, minted only via the TCB `LOGON_ON_BEHALF` path |
| `primary_group_sid` | The primary group SID |
| `credentials` | The typed credential set (§3.3) |
| `pw_last_set` | Timestamp of last password change |
| `last_logon` | Timestamp of last successful logon, written on the logon path (§5.1) |
| `pw_history` | Prior verifiers, for reuse prevention (§3.4) |
| `account_expires` | Account expiry instant, or "never" |
| `bad_pw_count`, `last_bad_pw_time`, `lockout_until` | Lockout state, mutated on the logon path (§5.1) |
| `claims` | Typed attributes for conditional ACEs |
| `posix_uid`, `posix_gid` | POSIX projection (uid if a user, gid if a group); derived and stored per §3.6. Supplementary gids are not stored — they are projected from the expanded group set at mint time (§3.6) |
| `security_descriptor` | The principal's KACS SD (PSD-004 §3, `ACL_REVISION_DS`) governing administrative access to this object — Reset Password, property writes, membership, delete (§7.2). Defaulted at creation by inheritance from the domain object's SD (§7.2); never crosses the seam (§2.2) |
| `created_at`, `modified_at`, `version` | Bookkeeping; `version` is an optimistic-concurrency counter |

The user SID, `object_guid`, and `rid` are immutable once assigned. The
`sam_account_name` MAY be changed; `object_guid` is the stable handle
that makes such a change safe.

On `CreateUser`, lpsd MUST set `primary_group_sid` to the BUILTIN Users
alias (`S-1-5-32-545`) and MUST add an explicit membership edge from
`BUILTIN\Users` to the new user. This default applies to ordinary users and
to purpose-made service accounts (§5.4). Later versions MAY add a separate
primary-group mutation verb, but v0.23 does not expose one.

## The group record

| Field | Meaning |
|---|---|
| `rid` | RID (for `machine_sid`-relative groups), or the fixed well-known SID for BUILTIN aliases |
| `object_guid` | Stable identity |
| `name`, `display_name` | Group name and display name |
| `group_type` | Security vs distribution, and scope. Retained for AD symmetry; for a standalone store a group is a domain-local security group |
| `member` | Forward membership links (§3.2 below) |
| `posix_gid` | POSIX projection |
| `security_descriptor` | The group's KACS SD (as for users; §7.2). For a group, the **Membership** property write is the add/remove-member gate |
| `created_at`, `modified_at`, `version` | Bookkeeping |

## Membership

Membership MUST be stored as forward `member` links on the **group**,
not as back-links on principals. `member` is the single source of
truth. A `member` entry MAY reference:

- a local user,
- another local group (nested membership), or
- a **foreign SID** (e.g. a domain principal placed into a local group).

lpsd computes a principal's expanded group set at resolution time
(§4, §5.1) by walking the `member` graph transitively. The walk MUST
detect and break cycles (e.g. group A a member of group B and B a
member of A) and MUST terminate. The result MUST be the full transitive
closure and MUST be identical regardless of traversal order; breaking a
cycle MUST NOT drop any principal reachable along it. Foreign-SID members
are included as-is (lpsd does not resolve them). Each expanded group
carries `SE_GROUP_MANDATORY | SE_GROUP_ENABLED | SE_GROUP_ENABLED_BY_DEFAULT`
(PSD-004).

> [!INFORMATIVE]
> Foreign-SID membership is how a domain principal acquires local-group
> rights: the broker queries lpsd for the local groups containing the
> principal's SIDs and merges them (§5.2), even though the principal
> itself lives in another source.
