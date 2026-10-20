---
title: Event Types
description: The form of an event type — root, nouns, past-tense verb, at least three segments — the segment grammar, platform roots and package-name roots, and why every dot is a policy anchor.
---

An event type reads left to right as who wrote it, what it is about, and
what happened:

```text
<root>.<noun>[.<noun>…].<verb>
```

`kacs.audit.access.checked`, `peinit.job.started` and
`org.jellyfin.server.playback.started` are event types.

## Form

An event type MUST have at least three segments: a root, at least one
noun, and a verb.

Every segment other than those of a package-name root (below) MUST match:

```text
[a-z][a-z0-9]*(-[a-z0-9]+)*
```

That is, lowercase ASCII, kebab-case within a segment, and no
underscores, capitals or empty segments. The event type MUST NOT contain
`/`.

## Roots

The root names the owner of the event type.

A **platform component** has a platform root of one segment, listed in
§6.A. A platform root names a component, not a package: several
components shipped in one package each have their own root. An emitter
MUST NOT use a platform root it is not listed against.

**Every other emitter** roots its event types at its own package name
(PSPU §5.3), split into segments at its periods. A package named
`org.jellyfin.server` writes `org.jellyfin.server.playback.started`.
This holds for first-party applications as much as for third parties.
An emitter MUST NOT root an event type at a package name that is not
its own.

A platform root MUST NOT be a top-level domain in the DNS root zone, so
that no platform root can be mistaken for the first segment of a
package name. `netd` is a valid platform root; `net` is not.

> [!NOTE]
> A package name may contain characters the segment grammar above does
> not admit — a leading digit, or `+`. Its segments are used as they
> are. A query naming such a type has to quote it, because the query
> language's unquoted identifiers start with a letter and exclude `+`
> (PSPU §3.19).

A consumer can derive an event type's owner from its name: a platform
root through §6.A, and a package-name root as the longest installed
package name its leading segments spell. A consumer MUST NOT treat the
root as evidence of who wrote the event. The record header is that
evidence (§6.4): nothing in this version prevents an emitter from
writing under a root it does not own.

> [!NOTE]
> Enforcing root ownership needs a way to prove which package a running
> program belongs to, which Peios does not yet have. It is left to a
> later attested-events mechanism rather than approximated now. Until
> then, review of a package submitted to the Peios package repository
> includes checking that its events use its own root.

## Nouns

After the root come one or more nouns, from general to specific.

An emitter SHOULD add a noun segment only where someone would plausibly
write a policy on the set of event types beneath it. A middle segment
that groups nothing anyone would grant, deny or switch off together
costs every name a segment and buys nothing; tidiness alone is not a
reason. The exception is a segment needed so that two event types do
not collide.

Depth is preferred to compounds: `lcs.audit.backup.started`, not
`lcs.audit.backup-started`. A compound word within a segment is for a
single concept that has no useful parent, such as `copied-up`.

## The verb

The last segment is a past-tense verb saying what happened: `created`,
`started`, `ended`, `checked`, `used`, `refused`.

The verb SHOULD be neutral where a neutral verb still says what
happened, and MUST NOT be so neutral that it does not. `installed` is
right for a package installation even when the installation failed,
because the failure is carried in `outcome.success` (§6.6) and any
consumer can show it. `transaction.ended` is wrong: it does not say what
the transaction was.

An action that can succeed or fail is **one** event type (§6.6). An
event type that is only ever written on failure MAY say so in its verb,
as `stratafs.mutation.refused` does.

Distinct steps of a lifecycle are distinct event types:
`peinit.job.created`, `peinit.job.started` and `peinit.job.ended` are
three things that happen, not three outcomes of one.

## Every dot is a policy anchor

A consumer that controls read access per event type resolves an event's
descriptor by trying the full type, then each shorter dotted prefix
(PSPU §3.28). A descriptor on `kacs.audit` therefore covers the audit
trail without the rest of KACS, and the emission policy is keyed the
same way (§6.9). This is why the noun rule above is about policy, and
why the segments are fixed rather than left to taste.

> [!NOTE]
> A form with a slash, `dev.peios.peinit/job.created`, was considered
> and rejected. In log origins a slash separates a producer from a part
> of it below policy granularity, and the descriptor resolver stops at
> the first slash. Every event type would then resolve only at its
> package, and the slash is not an identifier character in the query
> language, so every query would need quotes.
