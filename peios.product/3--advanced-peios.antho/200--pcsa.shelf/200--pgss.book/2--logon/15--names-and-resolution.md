---
title: Names and Resolution
description: A name is opaque to the client — comparison, reserved characters, qualified names, and the search order an authority applies.
---

## The name is opaque to the client

A name is carried as a single string. A client MUST forward what it was
given, unchanged, and MUST NOT parse, split, qualify, case-fold, or
otherwise interpret it.

All interpretation is the authority's.

This is the load-bearing rule of the section. If a client resolved part
of a name itself — chose which source to consult, or which of two
candidates wins — then that policy would live in every client
separately, and a native tool could resolve `jack` to a different
principal than a POSIX name resolver on the same machine. Two components
disagreeing about who a name refers to is not a display inconsistency;
it is a program acting on one principal's behalf while checking
another's access.

One authority means one answer, and it means a name resolves identically
here and in a logon (§2.7), because the same resolution serves both.

## Comparison

Name comparison is **ASCII case-insensitive**.

This is normative rather than each source's own choice, because a system
may have more than one source and they must not disagree about whether
`JACK` is `jack`. An authority MUST establish the comparison for itself
rather than delegate it to whatever a source happens to do.

## Reserved characters

A principal or group name MUST NOT contain any of:

| Character | Reserved for |
|---|---|
| `@` | Qualified names (below) |
| `\` | Qualified names, in the form some callers will type |
| `/` | Path separation — a name reaches a filesystem as a home directory |
| `:` | Field separation in POSIX `passwd` and `group` records |
| `,` | Member and subfield separation in POSIX `group` and GECOS records |

A name MUST NOT contain a byte outside the printable ASCII range
`0x20`–`0x7e`, and MUST NOT begin or end with a space.

An authority MUST refuse to create a name violating these rules, MUST
refuse one it is asked to resolve, and MUST refuse one asserted by a
source. The third is the one that matters: a name reaching a caller from
a source has crossed a boundary the other two never did, and it is the
one that ends up in a `passwd`-format record, an audit line, or a log.

The excluded control characters are the record separators. A name
carrying a newline could forge a whole line in a `passwd`-format file,
an audit record, or a log — and the damage is done by the reader, so it
cannot be prevented at the point the name is displayed.

The rules apply to every name an authority emits, including the names
carried alongside SIDs in references (§2.16), not only to the name a
request was keyed on.

> [!NOTE]
> The ASCII restriction is not an assumption that names are English. It
> is a decision to defer confusable and normalisation handling rather
> than get them wrong: `jack` spelled with a Cyrillic `а` renders
> identically to `jack` and is a different principal, and the same name
> in NFC and NFD is two byte sequences that a comparison will call two
> people. Relaxing this later is backward compatible; tightening it
> later would mean renaming principals that already exist.

## Qualified names

A name MAY be qualified with a realm, written `name@realm`.

**No realm syntax is defined in this version.** An authority MUST refuse
a name containing `@`, and the character is reserved so that a principal
literally named `jack@local` cannot come into existence before the
syntax does.

Nothing here changes when realms arrive: a qualified name is a different
string in the same field, parsed by the same authority. That is why the
field is one opaque string rather than a structured pair — a structure
would have put the parsing in the client, which the first rule of this
section forbids.

## Search order

A bare name is resolved by consulting sources in an order that is
**local configuration of the authority**.

An authority MUST resolve in a configured order, MUST NOT derive that
order from the order in which sources registered, and MUST stop at the
first source that answers.

> [!NOTE]
> Registration order is whatever the boot happened to do. Making it
> decide who `jack` is would mean a slow disk could change which
> principal a name refers to.

## Answers an authority holds itself

An authority MAY answer from its own knowledge, without consulting any
source. Well-known principals and groups — those whose SIDs are fixed by
the system rather than issued by anybody — are the ordinary case: their
names, and the fact that nothing records their membership (§2.16), are
properties of the system.

Such an answer is subject to every rule in this section. In particular
an authority MUST apply the reserved-character and comparison rules to
it, and MUST NOT return an answer for a name it would have refused.

An answer of this kind is not an outage and does not make a reply
`Unavailable`, whatever the state of the configured sources. It is also
not a source: an authority MUST NOT report it in the `incomplete` list
of an enumeration (§2.17), and MUST NOT count it as a source having
answered for the purpose of §2.18.

## Bare in, qualified out

Every successful reply carries the resolved **SID** and the **canonical
qualified name**, whatever form the request used (§2.16).

A caller that looked up a bare name can therefore always tell which
principal it got, compare two answers for identity, and record an
unambiguous name in a log. Ambiguity is permitted in what a caller may
ask; it is not permitted in what an authority answers.

Where no realm syntax exists, a canonical qualified name is
indistinguishable from a bare one, and the SID alongside it is what
carries the unambiguity. A client MUST NOT rely on the two being
distinguishable, in either direction: it MUST NOT assume a returned name
is unqualified, and MUST NOT treat one that is as a failure to
canonicalise.

## Shadowing

Adding a source ahead of another in the search order changes which
principal a bare name resolves to. The new principal has a different
SID, so every security descriptor naming the old one stops applying to
the person now signing in under that name.

This is inherent to a flat namespace and this chapter does not forbid
it. An authority SHOULD detect it at logon — where the cost is one
additional query per sign-in rather than one per lookup — and SHOULD
record that a bare name resolved while another source could also have
answered.

An authority MUST NOT fail a logon because it could not complete that
check. A source being unreachable is not a reason to refuse a principal
whose own source answered.
