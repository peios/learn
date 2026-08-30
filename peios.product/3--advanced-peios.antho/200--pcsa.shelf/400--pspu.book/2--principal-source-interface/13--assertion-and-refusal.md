---
title: Assertion and Refusal
description: "The two terminal messages a source may send — and what an assertion pointedly does not contain: no session, no token, no privileges."
---

Exactly one terminal message ends a source conversation.

## Assertion

`msg_type` = `0x8003`. Source to authority. **The only successful
outcome a source can produce.**

| Field | Encoding | Limit |
|---|---|---|
| `user_sid` | length-framed bytes (SID) | 68 bytes |
| `canonical_name` | string | 256 bytes |
| `groups` | array of group entries | 128 |
| `unix_id` | `u32` | §2.20 |
| `primary_group` | length-framed bytes (SID) | 68 bytes |
| `profile` | length-framed structure (PGSS §2.9) | |
| `claims` | array of claim entries | 64 |
| `permitted_logon_types` | `u32` | PGSS §2.16 |

Note what is absent: no session, no token, no privileges, no integrity
level. A source has no way to express them (§2.4).

Every field after `groups` is optional in the way §2.7 requires: a
source that does not write one has said nothing about it, and the
authority substitutes the default named below rather than failing.

### canonical_name

The source's own spelling of the principal's name. A client may have
typed `JACK`; this is what the principal is actually called.

Carrying it is what makes case-insensitive matching safe: the authority
records the canonical form rather than whatever was typed, so a
session's records do not vary with a caller's shift key.

A source MUST NOT assert a name that PGSS §2.15 forbids — one carrying a
reserved character, a byte outside the printable ASCII range, or a
leading or trailing space. The authority MUST refuse one anyway (§2.21),
because a name from a source reaches a `passwd`-format record and an
audit line, and by then the damage is the reader's to do.

The obligation is on what a source **asserts**, not on what it creates.
A source that validates a name when an administrator adds it, and not
when it reads one back from storage, has enforced nothing against a
store it did not itself write.

### permitted_logon_types

Which kinds of sign-on this principal may be used for, as the bitmask
PGSS §2.16 defines for the `LOGON_TYPES` field.

A source **states** the property and MUST NOT act on it. Deciding what
to do about a principal's restrictions is derivation, and derivation is
the authority's (§2.4) — a source that refused an authentication on
these grounds would be making an access decision it has no standing to
make, and would do it *differently* from the authority that also has to.

Zero means the source states nothing, and a source that does not hold
the property MUST send zero rather than inventing a value. In particular
it MUST NOT send "everything", which would assert that a principal may
be used for a credential-free service logon (PGSS §2.19) on no evidence
at all.

An appended field: a source predating it simply does not write it, which
the authority reads as zero and therefore as its own default.

### groups

Each entry is a separate length-framed structure:

| Field | Encoding | Limit |
|---|---|---|
| `sid` | length-framed bytes (SID) | 68 bytes |
| `unix_id` | `u32` | §2.20 |

**A SID and a number. No attributes.**

A source asserts *which* groups a principal belongs to. Whether a group
entry is enabled, owner-marked, or deny-only is a decision about how to
build a token, and building tokens is the authority's (§2.4). A source
saying "this principal is an administrator" is identity; a source saying
"and mark that group deny-only" would be reaching into derivation.

The per-entry framing is what allowed `unix_id` to be added here without
breaking a decoder that predates it, and it will allow the next field
the same way.

A `unix_id` of **0** means the source does not number this group — the
honest answer for a group it does not own. A source naming a well-known
group is stating a membership, not claiming authority over what that
group projects to; see §2.20.

### unix_id

The principal's POSIX identifier, **relative to the range the authority
assigned this source** (§2.20). Zero means the source has no number for
this principal.

A source MUST NOT apply its own base. It counts within its range and the
authority rebases; a source that added the base itself would have it
added twice.

### primary_group

Which of the principal's groups projects to the POSIX group id, and
becomes the default group of objects the token creates. Empty means the
source did not say, and the authority chooses.

It need not appear in `groups`. The authority is required to place it on
the token regardless (§2.21), because a token's primary group must be a
group the token carries — so naming a group here **is** a membership
claim, and it is subject to membership scope exactly as a listed group
is (§2.19).

That applies to a primary group the **source asserted**. Where the field
is empty and the authority substitutes one of its own, the substituted
value is the authority's choice and MUST NOT be tested against the
source's membership scope. Testing it would deny every logon from a
source that declined to name a primary group, on the strength of a claim
that source never made — and an authority's own default is very unlikely
to be a sibling of the principal's domain, so the test all but always
fails.

> [!NOTE]
> A source that made this the one field escaping the scope check would
> have found a route to `BUILTIN\Administrators` that the group array
> denies it. The obligation in §2.21 to apply membership scope to the
> primary group closes that.

### profile

PGSS Logon's profile structure (PGSS §2.9), relayed onward to the client
unchanged. It is not identity, it decides no access, and the authority
does not interpret it.

The one thing the authority does check is the one PGSS §2.9 requires of
it: `home` and `shell`, when non-empty, are absolute paths. That
obligation binds the authority towards its client whatever the value's
provenance, so a relayed profile is not exempt from it.

### claims

Named, typed attributes fed to conditional ACE evaluation, in the claim
attribute format PCDS §5.9 specifies. Each entry is a separate
length-framed structure:

| Field | Encoding | Limit |
|---|---|---|
| `name` | string | 255 bytes |
| `flags` | `u32` | PCDS §5.9 |
| `value_type` | `u32` | PCDS §5.9 |
| `values` | array of length-framed values | 64 |

A claim is the one field here that is a **trusted input to access
decisions** rather than a statement of identity: a conditional ACE can
turn a claim into a grant. Which claim names a source may assert is
therefore the same kind of question as which groups it may assert, and
belongs with membership scope (§2.19).

An authority MUST reject an assertion carrying a claim it cannot carry
to a token — an unsupported value type, a name containing an interior
NUL, a value exceeding its limit — rather than dropping the claim. The
reasoning is rule 3 below: a dropped claim signs the principal in
against a policy nobody stated.

### What the authority MUST do with an assertion

1. **Validate every SID** with a structural check before treating it as
   identity. Bytes from another process are bytes until checked, and the
   check belongs in the process that mints tokens rather than in the
   codec that moved them (§2.7). This includes SIDs carried *inside* a
   claim value.
2. **Enforce identity scope** (§2.18), **membership scope** (§2.19) —
   including over `primary_group` — and **numeric scope** (§2.20).
3. **Fail the logon** on a malformed group SID, an unusable claim, an
   invalid `canonical_name`, or a `unix_id` outside the source's range,
   rather than dropping it. Dropping would sign the principal in with
   authority the source did not state — a confusing way to be wrong at
   best, and for a claim, a silent change of the policy that will be
   applied to them. A source that cannot encode a SID is broken.
4. **Drop a logon SID from the asserted groups**, loudly. No source is
   authoritative for one: the kernel mints them per session, and this
   session's did not exist when the source answered. A source asserting
   one is either buggy or reaching for a *different* session's SID,
   which would forge membership of somebody else's logon.
5. **Drop duplicates**, first mention winning. A source asserting a
   group the authority also derives is redundant, not wrong.

Rules 4 and 5 drop rather than refuse because the token still ends up
correct, and refusing would punish a principal for a source's defect
without making anything safer. Rule 3 refuses because the token would
*not* end up correct.

**Rules 4 and 5 run before rule 2.** A logon SID is by construction
outside the principal's domain, so an authority that applied membership
scope first would refuse the logon that rule 4 says to survive by
dropping. Duplicates are the same shape of problem. The drops are about
what a source should never have sent; the scope tests are about what it
is permitted to claim, and only what survives the first is subject to
the second.

An authority MUST also place `primary_group` on the token even when the
source did not list it among `groups`, since a token's primary group
must be a group the token carries.

## Refusal

`msg_type` = `0x8004`. Source to authority.

| Field | Encoding | Limit |
|---|---|---|
| `denial` | `u32` | PGSS §2.B |
| `reason` | string | 512 bytes |

Reuses PGSS Logon's denial vocabulary rather than inventing a parallel
one, so that relaying a refusal outward needs no lossy translation.

A source MUST NOT distinguish an unknown principal from a bad credential
— by code, by reason, or by timing (PGSS §2.10, §2.12). The obligation
is the source's here, because the source is where the distinction exists
to be leaked.

> [!NOTE]
> A principal requiring no credential is a separate matter, and cannot
> be hidden: a conversation that reaches `Assertion` with no round at
> all says that the named principal exists and needs nothing. That is
> inherent in permitting a zero-round logon rather than a defect in this
> rule, and it is the reason a passwordless principal is a
> configuration decision rather than a convenience.

An authority MAY relay `reason` to the client and MAY replace it. It
MUST NOT relay a reason that reveals a distinction the source was
required not to make.
