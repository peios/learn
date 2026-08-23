---
title: Numeric Scope
description: Every unix_id a source asserts is rebased into the range it was granted, refused rather than clamped when out of range.
---

**A source's POSIX identifiers are relative. The authority assigns the
range and applies the base; a source is told its range but MUST NOT act
on it.**

Every `unix_id` in an `Assertion` — the principal's and each group's —
and every identifier in a `QueryResult` is an offset within a range the
authority assigned that source. The authority adds the base before the
number reaches a token or a caller.

This is the numeric counterpart of identity confinement (§2.18). That
section stops a source naming principals outside its namespace; this one
stops it *numbering* them outside its namespace.

## The range

An authority MUST assign each source a range, as a **base** and a
**count**, spanning `[base, base + count)`.

> [!NOTE]
> Mainline configures both per source in the registry, as `UnixIDBase`
> and `UnixIDCount` alongside the domain pin (§2.10). How the assignment
> is expressed is the authority's own design; what it must satisfy is
> this section.

An authority MUST reserve a band below every source's base for
identifiers of its own — well-known SIDs, service SIDs, confinement SIDs
— none of which come from any directory. The band has to be generous,
because the last of those categories has no bound.

## Rebasing

Given a relative identifier `r` from a source with range
`(base, count)`, the authority computes `base + r`, and MUST refuse to
produce a number at all when:

- `r` is **0**. Zero is not an identifier; it is how a source says it
  has no number for something. It MUST NOT become `base`.
- `r` is **at or past `count`**. The source has reached outside the
  range it was given.

A number the authority declines to produce projects as *unmapped*, which
the Peios Kernel TRM §3.10.1 defines.

## Refuse, never clamp

An out-of-range identifier MUST be refused. It MUST NOT be clamped to
the top of the range, and it MUST NOT be reduced modulo the count.

Both alternatives look like graceful degradation and are worse than a
refusal:

- **Clamping** puts two principals on one number, so a filesystem cannot
  tell them apart.
- **Wrapping** lands inside somebody else's range, so one source's
  principal projects as another source's.

The range is a boundary, not an offset, and the count is what makes it
one.

## Two numbers a source can never reach

Because the base sits above the reserved band and a relative identifier
cannot escape the count:

1. **uid 0.** It belongs to the authority's own table and is not
   reachable by adding a base to anything a source can send.
2. **Another source's numbers.** Whatever a source asserts, arithmetic
   confines it to its own range.

Neither depends on the source behaving. They hold because of what the
source is *able to express*.

## Well-known SIDs are not the source's to number

An authority MUST use its own identifier for any SID in its reserved
band, and MUST ignore whatever `unix_id` a source sent alongside it.

A source asserting `BUILTIN\Administrators` is stating a membership. It
is not claiming authority over what that group projects to, and
honouring a relative identifier there would place a well-known group
*inside that source's range* — where a second source could number
something else identically.

## The authority tells the source its range

A source is told its base and count at registration (§2.8). This is
informational and exists so an administration tool can show an operator
the identifier a principal will really project to, rather than the
relative number on disk.

**A source MUST NOT apply the base to what it asserts.** It is told the
range so it can explain itself, not so it can do the arithmetic. A
source that applied its own base would have it applied twice.

> [!NOTE]
> Keeping the base out of the source's stored records is what makes
> rebasing a configuration change rather than a data migration. An
> administrator moving a source's range edits two configuration values;
> nothing the source persists has to be rewritten, because nothing it
> persists was ever absolute.

Disclosure costs nothing that matters. What confines a source is not
ignorance of the base but the authority's refusal to accept a relative
identifier at or past the count — a check the authority performs on
every number it rebases, whatever the source knows.

## Uniqueness within a source

SIDs are one namespace; POSIX user and group identifiers are two. A
source MUST therefore allocate from a **single counter across every kind
of object it holds**, so that a number issued to a principal is never
issued again to a group.

An authority cannot check this — it sees one assertion at a time — so it
is stated as an obligation on the source (§2.21) rather than as
something enforced.

> [!NOTE]
> The simplest way to satisfy it is to make an object's identifier its
> relative identifier within the domain, which is already unique across
> principals and groups. That has the incidental benefit that one object
> has one number rather than two unrelated ones.
