---
title: Dependency resolution
type: how-to
description: Review dependencies, substitutions, removals, source and root changes; handle resolution failures and action-specific approvals.
related:
  - peios/package-management/overview
  - peios/package-management/installing-and-removing
  - peios/package-management/repositories-and-trust
  - peios/package-management/claims
  - peios/package-management/named-roots
  - peios/auditing/overview
---

A request to install one package can add dependencies, replace another
package or affect another root. The **plan** is the full change you are
approving. Use `--dry-run` on the intended install, upgrade, downgrade or
removal to inspect it before applying anything.

## The plan

Review these points before answering `proceed?`:

- Are all named packages and dependencies expected?
- Which versions and repositories will supply them? Does a local-file marker
  indicate that you are vouching for a file directly?
- Is a virtual name being satisfied by a different package than you expected?
- Will `replaces` or `--cascade` remove something you still need?
- Will claims move, or entries tagged `-> <root>` change another root?
- Does a downgrade or cross-repository takeover need a separate approval?

Decline the plan if any change is unexpected. Check repository configuration
and package details, change the request, and preview again. Do not assume
that the package named on the command line is the only package affected.

## When resolution refuses the request

Resolution rejects an unsatisfied dependency, conflicting packages, an
architecture mismatch, an ordering cycle or a graph that exhausts its work
budget. Read the named packages and constraints before retrying.

- Refresh and search the intended repositories if a package is unavailable.
- Correct a missing or untrusted repository rather than silently accepting
  another source.
- For a blocked removal, inspect the dependents. Use `--cascade` only if you
  intend to remove all of them.
- For a conflict, choose a compatible package set; there is no automatic
  conflict-removal approval that makes the rejected plan safe.
- For root-related errors, inspect the [root references](~peios/package-management/named-roots)
  and preview each affected target.

The [failure conditions](~peios/peipkg/resolution/failure-conditions) and
[removal-cascade reference](~peios/peipkg/resolution/removal-cascades) document
what is checked. Optional dependencies are not installed automatically;
name a wanted companion explicitly.

## Elevated authorisation

Most of a plan is routine, and the single `proceed?` prompt covers it. A plan can also contain an action that a routine yes should not cover — one you must review and approve individually, on its own.

peipkg detects three such actions and, for each one in a plan, asks a separate question:

```
this operation requires elevated authorisation:
  nginx would move backward from 1.27.5 to 1.27.4
authorise this specific action? [y/N]
```

The three actions that trigger it:

| Action | Why it is elevated |
|---|---|
| **A downgrade** | Moving a package backward can reintroduce a problem a newer version fixed. It should be a conscious choice, never a side effect of some larger plan. |
| **A foreign `replaces`** | A package from a *lower*-priority repository using `replaces` to displace a package you installed from a *higher*-priority one. Left unguarded, a low-trust repository could quietly take over a package you trusted a better source for. |
| **A low-trust `provides`** | A package from a low-trust repository advertising a virtual capability in a way that shadows a package from a more-trusted source — satisfying a dependency with its own build instead of the one you would expect. |

Two things make this prompt different from the routine one:

- **`--yes` does not satisfy it.** `--yes` skips the routine `proceed?` prompt; it has no effect on an elevated-authorisation question.
- **End-of-input refuses it.** A closed input cancels the action. This is not a separate authentication channel: the [authorisation reference](~peios/peipkg/security/operator-authorisation#the-channel-is-not-distinguished) documents that piped affirmatives can answer the same questions. Do not pipe blanket approvals as a substitute for reviewing elevated actions.

Each elevated action is presented and authorised on its own; approving one does not approve the next. And the authorising act is itself written to the [audit stream](~peios/auditing/overview) — the record shows not just what was done, but that it was specifically authorised and what was authorised.

If an elevated action is not one you want, the plan as a whole is the thing to reconsider: where the package is coming from, whether the repository priorities are right, whether the downgrade is really what you meant.

## The relationships between packages

A package's manifest declares how it relates to others. Four relationships drive resolution.

**Dependencies.** A package can require other packages, each by a version range. peipkg pulls every dependency into the plan, and their dependencies in turn, until the request is closed.

**Conflicts.** A package can declare that it cannot coexist with another. If a plan would put two conflicting packages on the system at once, resolution rejects it.

**Provides.** Several packages can advertise the same capability — a **virtual** name that is not itself a package. A dependency written against that name is satisfied by any package that provides it. This is how "needs a mail transport agent" can be met by whichever one you actually install.

You can ask for a virtual name directly, too: `peipkg install coreutils` works even when nothing is named `coreutils`, and installs whichever package provides it. Because you asked for one name and got a package with another, peipkg says which one it chose. Upgrades and removals are the exception — those name a package you already have, so they match by name only and never substitute one package for another.

**Replaces.** A package can declare that it supersedes another — the usual case being a rename, or a merge of two packages into one. Installing a package that `replaces` another causes the replaced package to be removed as part of the same plan.

`provides` has a stronger cousin: a **claim**, a single shared name that exactly one package may hold at a time. Where any number of packages can advertise the same `provides` name at once, a claim has one holder — see [Claims](~peios/package-management/claims).

A dependency can also be routed into a different root, written `Depends: foo IN <root>`, so that a whole root can be composed through the dependency graph — see [Named roots](~peios/package-management/named-roots).

## Choosing a version

Selection depends on version constraints, architecture, repository origin
and priority, and whether a name is a concrete package or a virtual
capability. For upgrades, the installed version is the starting point; a
plan with no update may reflect its constraints and available sources.

> [!NOTE]
> Existing descriptions differ on whether version or repository priority
> wins first. The detailed [candidate-selection reference](~peios/peipkg/resolution/candidate-selection)
> places architecture and source preferences before version, while earlier
> operator guidance described highest version first. Inspect the actual plan;
> this guide does not promise that the newest version across all repositories
> will win. The reference keeps the ordered rules and virtual-version handling.

## Resolution is a pure calculation

Resolution uses metadata rather than downloading package payloads. It produces
a plan or explains why no plan was found. A dry run is a preview of those
inputs, not a reservation: refreshing a repository or changing the installed
set before applying can change the result. Review the final plan too.

See [Inputs and outputs](~peios/peipkg/resolution/inputs-and-outputs) for the
resolver's inputs, ordering and determinism discussion, and
[Candidate selection](~peios/peipkg/resolution/candidate-selection) for its
selection and tie-breaking rules. The implementation is bounded and can
return a `too complex` rejection rather than continue indefinitely.

## Where to go next

- [Apply an install or removal](~peios/package-management/installing-and-removing)
- [Check repository trust and priority](~peios/package-management/repositories-and-trust)
- [Choose a claim holder](~peios/package-management/claims)
