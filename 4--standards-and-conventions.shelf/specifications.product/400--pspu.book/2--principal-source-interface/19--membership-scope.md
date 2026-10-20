---
title: Membership Scope
description: Group membership is the one legitimate exception to confinement — the default, the exception, and why it never extends to identity.
---

Group membership is the question with a legitimate exception, and it
needs one.

## The default

By default, an authority MUST refuse an `Assertion` carrying a group
outside the domain of the principal being asserted.

A directory vouches for its own users and its own groups, and nothing
else. Without this rule, a directory-backed source could declare its
users members of `BUILTIN\Administrators` — making a remote authority
the arbiter of who administers this machine.

The test is *relative*: are the group and the principal in the same
domain? It needs no configuration and no knowledge of which domain
belongs to whom, which is why membership scope is enforceable before
anything else about scope is settled.

## The exception

An authority SHOULD allow a source to be configured as permitted to
assert **memberships** outside the asserted principal's domain.

A local source needs it. Local group membership of *any* principal is a
local decision: "`CORP\Domain Admins` is in `BUILTIN\Administrators`" is
a record this machine keeps, not something a domain controller asserts
at it. Without the exception, a local source could not express the one
thing it is most authoritative about.

An authority MAY grant this to more than one source. Nothing about it is
exclusive.

## Memberships only, never identity

A source holding this permission **remains fully confined on identity**
(§2.18).

The two are separate because the risks are not symmetric. A source
asserting a foreign *membership* is making a claim about what a
principal may do **on this machine**, which is a local matter and is the
local source's business. A source asserting a foreign *identity* is
claiming to be the authority for somebody else's principal, which is
never anyone's business but that authority's.

> [!NOTE]
> Specifying the permission narrowly — memberships only — from the
> outset is what allowed identity confinement to be switched on later
> without changing what the setting means. A permission defined as "this
> source is trusted" would have had to be redefined, and every existing
> configuration reinterpreted, the day identity scope arrived.

## The primary group is a membership

`primary_group` (§2.13) is subject to this section exactly as a listed
group is, and an authority MUST apply the test to it.

It would otherwise be a way round: the authority is required to place
the primary group on the token whether or not the source listed it, so a
source that named `BUILTIN\Administrators` there and nowhere else would
obtain a membership the group array denies it.

An authority that adds an unlisted `primary_group` to the membership set
MUST do so **before** applying this section, not after. Adding it
afterwards reintroduces exactly the route the rule closes.

This binds a primary group the **source asserted**. A default the
authority substituted for an empty field is not the source's claim and
MUST NOT be tested against the source's scope (§2.13); an authority that
tested its own default would refuse every logon from a source that
simply left the field empty.

## Claims are the same question, unanswered

A claim (§2.13) is a trusted input to conditional ACE evaluation, so
asserting one can produce a grant just as asserting a membership can.
*Which claim names a source may assert* is therefore the same shape of
control as this section — and it is **not yet specified**.

The gap is stated rather than papered over. An authority federating to a
source it does not fully trust should consider claims as it considers
foreign memberships, and a future revision is expected to define the
control here.

> [!NOTE]
> Active Directory splits this in a way worth borrowing: claim *type
> definitions* are forest-level configuration while claim *values* are
> per-user attributes. The equivalent split — the machine decides which
> claims exist, the source supplies values for them — is the obvious
> shape for the control, and is why this is a gap in configuration
> rather than a flaw in the message format.
