---
title: Eligibility
description: What makes a package an eligible provider of a role — what peipkg checks, and what it deliberately does not.
---

A package is an **eligible provider** of a role when it has a `provides`
entry naming the role whose `claims` field declares a target for at
least one slot. Only an eligible provider can hold a role.

A package that depends on a role and declares a claim path for it,
without providing the role, is a **consumer only**: it contributes paths
and can never hold.

## What peipkg checks

The declaration shape is validated on both sides. A consumer-side slot
descriptor carries a path and no target; a provider-side one carries a
target and optionally a path. A `claims`
field on a `conflicts` entry is rejected outright. Slot names are
validated against the package-name grammar.

Claim paths and targets are held to the payload path-syntax and safety
rules of §5.13 — absolute, valid UTF-8 in Normalization Form C, no NUL,
control or backslash bytes, no empty, `.` or `..` component, and within
the component, depth and total length limits. The manifest decoder
applies the same single copy of those rules that the archive reader
applies to a payload path, so the two cannot drift.

A claim **path** is also confined to the locations §5.23 admits: under
one of the permitted install destinations of §5.14, under `/run/`, or
the root-level name `/init`. A manifest declaring a claim path anywhere
else — `/etc/passwd`, `/opt/tool`, `/run` itself, `/init/x` — is
rejected when it is decoded, before anything is planned. A provider's
**target** is confined to the §5.14 destinations alone, because it
names a payload path: `/run/` and `/init` are claim-only locations that
no package can ship to.

## Targets are checked against the package's own payload

A provider's target must name a path the declaring package itself
installs, and peipkg checks that at install time against the payload it
actually received. The producer-side library offers the same check and
pekit runs it, but a producer-side check is a lint: it says nothing
about a package built anywhere else, which the format explicitly
contemplates.

The check also constrains targets by destination for free. A target that
must be a payload path inherits the payload path rules, because those
are enforced on the same entries.

## What peipkg does not check

`/lcl/policy` is unreachable as a claim path or target whatever else
permits it (§5.14), and the destination set keeps a claim link inside
the managed tree. Within that tree, materialising a link does not apply
the unowned-file rule that a payload entry gets (§5.7): a file at the
claim path that no package owns is displaced into the backup the
transaction keeps for rollback, and the commit then discards that
backup. Only a path owned by an installed package is refused (§9.6).
