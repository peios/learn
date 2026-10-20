---
title: Outcomes
description: The outcome every identity-channel reply carries — NotFound, Unavailable and Refused — and why these are not a security boundary.
---

Every reply on the identity channel carries an outcome.

| Value | Name | Meaning |
|---|---|---|
| 1 | `Found` | The request was answered. |
| 2 | `NotFound` | No such object, and every source that could have said so was asked. |
| 3 | `Unavailable` | A source that could have answered did not. |
| 4 | `Refused` | The caller may not make this request. |
| 5 | `Malformed` | The request could not be understood. |

Unlike the denial codes of §2.10, these are not a security boundary.
`NotFound` reveals that a name is unused, which is what a name lookup is
for.

An `EnumerateReply` carries an outcome on the same terms. An authority
MUST NOT report `Found` on a page it could not produce.

## NotFound and Unavailable

**If any source that could have answered was unavailable, the outcome is
`Unavailable` — even if every source that did answer said no.**

This is the most important rule in this part of the chapter, and it is
stated normatively rather than left to implementations because it is
invisible when wrong.

An authority is expected to cache. A cache that is told `NotFound` will
store an absence, and if that absence was really a source being
unreachable, it has memoised an outage as a fact. The account comes back
when the source does; the cached answer does not. A principal is then
unable to sign in, or a file is shown as owned by a number, for as long
as the entry lives — with nothing in the system still recording that
anything failed.

`Unavailable` is not cacheable, and that is the whole of the difference.

An authority MUST NOT report `NotFound` unless every source in the
search order (§2.15) that could have answered was consulted and
answered. A source that does not serve lookups at all is not such a
source and does not need to be asked; a source that does, and could not
be reached, is.

> [!NOTE]
> The rule binds even where an authority does not cache, because its
> clients may. A name resolver is entitled to remember an answer for the
> length of a process, and it can only do that safely if the two are
> distinguishable.

## Unavailable and the search order

An authority MUST consult sources in the configured order and MUST stop
at the first that answers, so an unreachable source **later** in the
order does not make an answer `Unavailable`. It was never going to be
asked.

An unreachable source **earlier** in the order does, even if a later one
holds a matching name — because the earlier source is the one whose
answer would have won.

> [!NOTE]
> Returning the later source's principal in that situation would be
> worse than failing. The name would resolve to a different SID than it
> does when the system is healthy, so access decisions would be made
> against the wrong principal precisely while something is broken.

## Refused

Reserved. No field in this version is restricted by default, and an
authority that restricts none will never send it.

It exists because the field mask (§2.16) is where restriction belongs,
and a request refused in its entirety needs an answer that is not
`NotFound`. An authority restricting a *field* MUST use the `Restricted`
withheld reason instead, and MUST still answer the rest of the request.

Because it is reserved, `Refused` MUST NOT be used for anything else. A
source that will not answer, a mode an authority has not implemented, or
a question it cannot serve are not the caller lacking permission, and
reporting them as `Refused` tells a client to stop asking on behalf of
this caller when the answer would be the same for every caller. Those
outcomes are `Unavailable`, `Absent`, or `Malformed` as the case
requires.

An authority MUST NOT use `NotFound` in place of `Refused` or of a
restricted field. Concealing a principal's existence from a caller that
may not read their shell protects nothing — the SID is already in the
file listing that prompted the lookup — and would make an authorization
decision indistinguishable from an empty system.

## Timing

The prohibition in §2.10 on distinguishing an unknown principal from a
bad credential does not apply here. There is no credential, and
`NotFound` is an ordinary answer that this chapter states plainly.

An authority MUST NOT allow the *presence* of an answer in a cache to be
observable to a caller that would be refused the answer itself. Where no
field is restricted, nothing is refused, and the requirement is vacuous.
