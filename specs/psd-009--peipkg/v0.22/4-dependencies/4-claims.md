---
title: Claims
---

A package's `provides` (§4.1.4) lets several installed
packages satisfy the same virtual name. A *claim* extends
that idea to the filesystem: it lets several installed
packages contend for a single shared filesystem name, with
exactly one of them owning it at a time. The canonical
example is a role daemon — `loregd` and an alternative
registry source may both be installed, but only one may own
`/usr/bin/registryd`.

This section defines claims, the manifest fields that declare
them, and how the package manager materialises a claim on
the filesystem. The operations that grant, revoke, and
withdraw a claim are defined in §7.7.

## Concepts

- **Role**: a virtual name (§4.1.4) that one or more packages
  contend to own. A role is identified by the `name` of a
  `provides` or dependency entry that carries a `claims`
  field. `registryd` is a role.
- **Slot**: a named channel within a role. A role has one or
  more slots; each slot materialises one filesystem name.
  `binary` is a slot of the `registryd` role.
- **Claim path**: the absolute filesystem path a slot
  materialises at (`/usr/bin/registryd`). A slot MAY have
  more than one claim path.
- **Target**: the file a claim path points at while a given
  provider holds the slot (`/usr/bin/loregd`). The target is
  a payload file of the holding package.
- **Holder**: the single installed package that currently
  owns a role. The holder's targets fill every one of the
  role's claim paths. A role has at most one holder at a
  time.

> [!INFORMATIVE]
> The two halves of a claim are declared by two different
> parties. The *consumer* — whatever hard-codes
> `/usr/bin/registryd` and expects to find a registry daemon
> there — declares the claim path. The *provider* — `loregd`
> — declares the target, the file of its own that should
> answer that path. The package manager joins the two by
> (role, slot) and creates the symlink. Splitting the
> declaration this way puts the path where the dependency on
> it lives and the target where the implementation lives.

## Declaration

A claim is declared by adding a `claims` field to a
dependency entry (§4.1.1), an optional-dependency entry, or a
`provides` entry (§4.1.4).

The `claims` field is an object mapping a slot name to a slot
descriptor:

```json
"claims": {
  "<slot name>": { "path": "<absolute path>",
                   "target": "<absolute path>" }
}
```

A slot name MUST conform to §2.1. A slot descriptor has two
OPTIONAL fields:

| Field | Type | Description |
|---|---|---|
| `path` | string | An absolute claim path the slot materialises at — the location of the symlink. |
| `target` | string | An absolute path to a payload file of the declaring package — what the symlink points at while this package holds the role. |

Which fields are permitted depends on where the `claims`
field appears:

- On a **dependency** or **optional-dependency** entry (the
  consumer side), each slot descriptor MUST contain `path`
  and MUST NOT contain `target`. A consumer declares only
  where it expects the name; it supplies no implementation.
- On a **`provides`** entry (the provider side), each slot
  descriptor MUST contain `target` and MAY contain `path`. A
  provider declares the file that answers the slot, and MAY
  additionally declare a default claim path (§4.4.4).

A `target` MUST name a path that the declaring package itself
installs as a payload entry (§3.5.1); it MUST therefore lie
within the permitted-install-path set of §3.4.1. A `target`
that does not correspond to one of the package's own payload
paths is INVALID and MUST cause the package to be rejected.

A `path` is the location of a manager-managed claim link, not
a payload entry, and is governed by its own location rule: it
MUST satisfy the payload path-syntax and safety constraints
of §3.2.7, and MUST lie within the §3.4.1 permitted-install-
path set or under `/run/`. The `/run/` allowance accommodates
runtime handles — sockets and the like — that conventionally
live there.

> [!INFORMATIVE]
> The link location and the target are constrained
> differently because they are different kinds of object. A
> target is a real file the provider ships, so it obeys the
> ordinary payload rules. A claim path is a name the package
> manager owns and points at that file; permitting `/run/`
> for it — without permitting packages to ship payload there
> — lets a role expose a runtime socket (`/run/logsink.sock`)
> while keeping `/run` off-limits to package payloads.

Example — `peinit` consumes the role, `loregd` provides it:

```json
// peinit's manifest (consumer)
"dependencies": [
  { "name": "registryd",
    "claims": { "binary": { "path": "/usr/bin/registryd" } } }
]

// loregd's manifest (provider)
"provides": [
  { "name": "registryd",
    "claims": { "binary": { "target": "/usr/bin/loregd" } } }
]
```

The slot keys within a `claims` object are an unordered JSON
object and carry no ordering requirement. The enclosing
`dependencies`, `optional_dependencies`, and `provides`
arrays remain sorted and unique by `name` per §4.1.7.

## Eligibility

A package is an *eligible provider* of a role when it has a
`provides` entry whose `name` is the role and whose `claims`
field declares a `target` for at least one of the role's
slots. Only an eligible provider may become the holder of a
role (§7.7).

A package that depends on a role and declares a claim `path`
for it, but does not provide the role, is a *consumer only*:
it contributes claim paths but can never hold the role.

## Materialisation

When a package holds a role, the package manager
*materialises* the role: for every slot of the role it
creates a symbolic link at each of the slot's claim paths,
pointing at the holder's target for that slot.

The set of claim paths for a slot is the union of:

- every `path` declared for that slot by an installed
  consumer (a dependency or optional-dependency entry,
  §4.4.2), and
- the `path` declared for that slot by the holder's own
  `provides` entry, if present.

> [!INFORMATIVE]
> The provider-declared `path` is a default: it lets a role
> materialise at a conventional location even when no
> installed package declares a dependency-side claim for it —
> a daemon a human invokes by name at a shell, say, with
> nothing in the package graph hard-coding the path. When at
> least one consumer declares a path, the consumer's and the
> provider's paths are both materialised (their union).

The materialised links for a role are a function of current
system state: the set of links MUST at all times equal the
cross-product of the role's computed claim paths (above) with
the holder's targets. The package manager MUST re-evaluate
this set — creating newly-required links, removing orphaned
links, and repointing changed links — within any transaction
that changes its inputs: a change of holder (§7.7.5, §7.7.6),
or the installation or removal of a package that declares a
claim path or a target for the role (§7.7.1, §7.7.6). This
re-evaluation is *reconciliation*; it is idempotent, so
reconciling against unchanged state produces no filesystem
change.

A held role whose computed claim-path set is empty
materialises no links yet remains held: the holder is
recorded in the package database (§7.7.4) independently of
whether any link exists. If a package that declares a claim
path for the role is installed later, reconciliation
materialises the link retroactively, against the holder
already on record — the holder is not re-decided.

> [!INFORMATIVE]
> A sole provider installed before any consumer is
> *held but unmaterialised*: `loregd` holds `registryd`, but
> until some package declares a dependency-side path (or
> `loregd` itself declares a provider default), there is no
> `/usr/bin/registryd` to point anywhere. Installing `peinit`
> — which declares the path — does not re-open the question
> of who holds the role; it only contributes a path, and
> reconciliation creates the link against the recorded
> holder. This is why holder state is tracked in the database
> independently of link existence.

A claim link is **owned and managed by the package manager**,
not by any package. A claim link MUST NOT appear in any
package's payload (§3.5.1) and MUST NOT be recorded as a
package-owned path (§7.1.5). This is what lets two eligible
providers coexist: neither ships `/usr/bin/registryd`, so the
one-package-per-path rule (§3.4.10) is never engaged by the
providers themselves.

A claim path MUST NOT collide with a path owned by any
installed package. Before materialising a claim link, the
package manager MUST verify that no installed package owns
the claim path (§3.4.10); if one does, materialisation MUST
fail with an explicit error and the containing transaction
MUST be rolled back (§7.5).

A claim link MUST be created using the same TOCTOU-safe path
resolution mandated for payload extraction (§7.1.2.3 step 1).
The holder's `target` MUST resolve to a path the holder owns
at the time of materialisation.

## One holder per role

A role has at most one holder at any time. The holder's
targets fill all of the role's claim paths; a role is never
partly held by one provider and partly by another.

Changing a role's holder — promoting a different eligible
provider — is a single operation: the package manager
repoints every one of the role's claim links from the old
holder's targets to the new holder's targets. Each repoint
MUST be atomic (create the new link at a temporary path, then
`renameat2` over the old link, §7.1.2.3) so that no consumer
of a claim path ever observes the path absent. The repoint of
all of a role's links MUST occur within a single transaction
(§7.4).

> [!INFORMATIVE]
> Atomic repoint matters because a claim path is typically on
> the critical path of a running system: `/usr/bin/registryd`
> may be exec'd by a service supervisor at any moment.
> Tearing the old link down and building the new one as two
> steps would expose a window with no `registryd`; the
> rename-over makes the swap instantaneous.

A role MAY be *unheld*: zero installed providers hold it. An
unheld role materialises no claim links, and its claim paths
simply do not exist. A dependency on an unheld role is still
satisfied at resolution time by any eligible provider that is
installed (§4.4.6) — primacy governs the filesystem name, not
dependency satisfaction.

## Relationship to resolution

Claims are orthogonal to dependency resolution (§4.2). Adding
a `claims` field to a dependency entry does NOT change
whether or how that dependency is satisfied: satisfaction is
determined solely by name, constraint, and architecture
(§4.2.3), exactly as for a dependency with no `claims` field.

In particular:

- A dependency on a role is satisfied by any installed
  eligible provider, whether or not that provider currently
  holds the role.
- Which provider holds the role has no effect on the
  resolver's candidate selection (§4.2.4).
- A package MAY depend on a role solely to declare a claim
  path for it, relying on the resolver's ordinary `provides`
  matching to ensure some provider is present.

> [!INFORMATIVE]
> Keeping claims out of resolution is deliberate: resolution
> decides what is *installed*; claims decide which installed
> file owns a contended *name*. Conflating them would make
> the resolver's result depend on mutable post-install
> filesystem state, which §4.2.8 (determinism) forbids.

## Optional claim consumers

A claim path declared on an `optional_dependencies` entry
(§4.1) is an *optional claim consumer*. The dependency need
not be satisfied for the consuming package to install
(§4.2.6), and the claim path is materialised only if and when
an eligible provider holds the role.

> [!INFORMATIVE]
> Example: `peinit` would use a log sink if one exists but
> ships without one. It declares
> `{ "name": "logsink", "claims": { "sink": { "path":
> "/run/logsink.sock" } } }` in `optional_dependencies`.
> `peinit` installs with no provider present and
> `/run/logsink.sock` is not created. Installing `eventd` —
> which provides `logsink` — lets `eventd` claim the role
> (§7.7), at which point `/run/logsink.sock` is materialised
> against `peinit`'s declared path. Removing `eventd` again
> withdraws the claim with no effect on `peinit`.

The distinction between a required and an optional claim
consumer governs the safety of withdrawing a role's holder
(§7.7.6): withdrawing a role on which only optional consumers
depend cannot break a required dependency.

## Resource limits

The claims mechanism is bounded by the resource limits of
§3.2 — the number of slots per `claims` field and the number
of claim paths materialised per role. A manifest whose
`claims` field exceeds these limits is INVALID and MUST be
rejected.

## What claims are not

Claims are NOT:

- A general symlink mechanism. A package that needs a fixed
  symlink among its own files ships it as a payload symlink
  entry (§3.2.6), not as a claim. Claims exist for names
  *contended by multiple packages*.
- A service-registration or service-activation mechanism. A
  materialised claim link is a filesystem symlink and nothing
  more; it starts no process and registers nothing with
  peinit (§4.3, "What side effects are not").
- A dependency-resolution input (§4.4.6).
- A way to escape the one-package-per-path rule (§3.4.10) for
  ordinary payload files. Only package-manager-owned claim
  links are exempt, and only at claim paths that no package
  owns.
