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

Claim paths and targets are checked for structural sanity: absolute,
within the length limit, lexically clean, with a non-empty first
component.

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

A claim **path** is not checked against the permitted install
destinations, and neither a path nor a target is subject to the payload
path-syntax constraints — normalisation form, control characters,
backslashes, component length. The one absolute exception is
`/lcl/policy`, which no claim path may reach (§5.14).

The visible consequence is that a claim path outside the managed tree is
materialised there, displacing whatever was at that path into a backup
that the commit then discards.
