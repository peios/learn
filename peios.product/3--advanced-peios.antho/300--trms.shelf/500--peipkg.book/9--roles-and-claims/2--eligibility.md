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

## What peipkg does not check

Neither a target nor a claim path is checked against the permitted
install destinations, and neither is subject to the payload path-syntax
constraints — normalisation form, control characters, backslashes,
component length.

A target is not checked against the declaring package's own payload
either. The producer-side library offers that check and pekit runs it,
but peipkg does not run it at install time, so a package built by
anything else can declare a target it does not ship.

The visible consequences, in order of severity: a claim path outside the
managed tree is materialised there, displacing whatever was at that path
into a backup that the commit then discards; a target naming a path the
package does not own produces a link pointing at whatever is there; and
a target naming nothing produces a dangling link.
