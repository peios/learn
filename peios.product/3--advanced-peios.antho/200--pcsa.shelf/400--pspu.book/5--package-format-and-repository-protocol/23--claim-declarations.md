---
title: Claim Declarations
description: How several installed packages contend for one shared filesystem name with exactly one owning it — the vocabulary, eligibility, and the consumer's part.
---

`provides` (§5.21) lets several installed packages satisfy one virtual
name. A **claim** extends that to the filesystem: it lets several
installed packages contend for a single shared filesystem name, with
exactly one owning it at a time. The canonical case is a role daemon —
two registry sources may both be installed, but only one may own
`/usr/bin/registryd`.

This section specifies what a package declares. Which provider holds a
role, and when the consumer re-evaluates that, is consumer mechanics.

## Vocabulary

- **Role** — a virtual name (§5.4) that one or more packages contend to
  own. A role is identified by the `name` of a `provides` or dependency
  entry carrying a `claims` field.
- **Slot** — a named channel within a role. Each slot materialises one
  filesystem name. A role has one or more slots.
- **Claim path** — the absolute path a slot materialises at. A slot MAY
  have more than one.
- **Target** — the file a claim path points at while a given provider
  holds the slot. The target is a payload file of the holding package.
- **Holder** — the single installed package that currently owns a role.
  A role with no holder is *unheld*.

> [!NOTE]
> The two halves of a claim are declared by two different parties. The
> *consumer* — whatever hard-codes `/usr/bin/registryd` and expects to
> find a registry daemon there — declares the path. The *provider*
> declares the target, the file of its own that should answer it. The
> consumer joins the two by (role, slot). Splitting the declaration this
> way puts the path where the dependency on it lives and the target
> where the implementation lives.

## The `claims` field

A claim is declared by adding a `claims` field to a dependency entry, an
optional-dependency entry, or a `provides` entry. It maps a slot name to
a slot descriptor:

```json
"claims": {
  "<slot name>": { "path": "<absolute path>",
                   "target": "<absolute path>" }
}
```

A slot name MUST conform to the package-name grammar (§5.3).

Which of the two descriptor fields is permitted depends on where the
`claims` field appears:

- On a **dependency** or **optional-dependency** entry — the consumer
  side — each slot descriptor MUST contain `path` and MUST NOT contain
  `target`. A consumer declares only where it expects the name; it
  supplies no implementation.
- On a **`provides`** entry — the provider side — each slot descriptor
  MUST contain `target` and MAY contain `path`. A provider declares the
  file that answers the slot, and MAY additionally declare a default
  claim path.

A `claims` field MUST NOT appear on a `conflicts` or `replaces` entry.

Slot keys within a `claims` object are an unordered JSON object and
carry no ordering requirement. The enclosing arrays remain sorted and
unique by `name` (§5.21).

Example — one package consumes the role, another provides it:

```json
// the consumer's manifest
"dependencies": [
  { "name": "registryd",
    "claims": { "binary": { "path": "/usr/bin/registryd" } } }
]

// the provider's manifest
"provides": [
  { "name": "registryd",
    "claims": { "binary": { "target": "/usr/sbin/loregd" } } }
]
```

## Where a target may point

A `target` MUST name a path the declaring package itself installs as a
payload entry, and MUST therefore lie within the permitted install
destinations of §5.14. A `target` that does not correspond to one of the
declaring package's own payload paths is invalid and MUST cause the
package to be rejected.

A consumer MUST verify this itself, against the payload it actually
received. Producer-side validation says nothing about a package built
elsewhere.

## Where a claim path may lie

A claim path is not a payload entry — it is the location of a
consumer-managed link — and is governed by its own rule. It MUST satisfy
the payload path-syntax and safety constraints of §5.13, and it MUST lie
in one of:

- the permitted install destinations of §5.14;
- under `/run/`; or
- the well-known root-level name `/init`.

Any other location MUST cause the package to be rejected.

> [!NOTE]
> A link location and a target are constrained differently because they
> are different kinds of object. A target is a real file the provider
> ships, so it obeys the ordinary payload rules. A claim path is a name
> the consumer owns and points at that file; permitting `/run/` for it —
> without permitting packages to ship payload there — lets a role expose
> a runtime socket while keeping `/run` off-limits to package payloads.
> `/init` is admitted for the same reason in the other direction: it is
> a well-known file a provider must own directly, and it is not a
> payload destination.

`/lcl/policy` MUST NOT be reachable as a claim path under any
circumstance, by the same rule and for the same reason as §5.14.

## Eligibility

A package is an **eligible provider** of a role when it has a `provides`
entry whose `name` is the role and whose `claims` field declares a
`target` for at least one of the role's slots. Only an eligible provider
may hold a role.

A package that depends on a role and declares a claim path for it, but
does not provide the role, is a **consumer only**: it contributes claim
paths and can never hold.

## What a consumer guarantees

The materialised links for a role MUST at all times equal the
cross-product of the role's computed claim paths with the holder's
targets, where the computed claim path set for a slot is the union of:

- every `path` declared for that slot by an installed consumer, and
- the `path` declared for that slot by the holder's own `provides`
  entry, if present.

A consumer MUST re-evaluate that set within any transaction that changes
its inputs — a change of holder, or the installation or removal of any
package declaring a claim path or a target for the role. A claim path
declared for an already-held role MUST be materialised retroactively
against the current holder; the holder is not re-decided.

A role MAY be held with no materialised links at all, when its computed
path set is empty. Holder state is therefore recorded independently of
whether any link exists.

A claim link is owned by the consumer, not by any package. It MUST NOT
appear in any package's payload and MUST NOT be recorded as a
package-owned path. This is what lets two eligible providers coexist:
neither ships the contended path, so the one-package-per-path rule
(§5.16) is never engaged by the providers themselves.

A claim path MUST NOT collide with a path owned by any installed
package, evaluated against the state the containing transaction will
produce rather than the state it started from. On collision,
materialisation MUST fail and the transaction MUST be rolled back.

A holder swap MUST repoint every one of the role's links within a single
transaction, and each repoint MUST be atomic, so that no consumer of a
claim path ever observes the path absent.

> [!NOTE]
> Atomic repoint matters because a claim path is typically on the
> critical path of a running system: a contended daemon binary may be
> executed at any moment. Tearing the old link down and building the new
> one as two steps exposes a window in which the name does not exist.

## What claims are not

- Not a general symlink mechanism. A package needing a fixed symlink
  among its own files ships a payload symlink entry (§5.17). Claims
  exist for names contended by several packages.
- Not a service-registration or activation mechanism. A materialised
  claim link is a symlink and nothing more.
- Not an input to dependency resolution (§5.21).
- Not a way to escape the one-package-per-path rule for ordinary payload
  files. Only consumer-owned claim links are exempt, and only at paths
  no package owns.
