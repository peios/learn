---
title: Dependency resolution
type: concept
description: Before any change, peipkg resolves a request into a concrete plan — which versions of which packages, in what order. This page covers dependencies, conflicts, provides and replaces, how a version is chosen, and the elevated-authorisation prompt that guards the few actions a routine yes should not cover.
related:
  - peios/package-management/overview
  - peios/package-management/installing-and-removing
  - peios/package-management/repositories-and-trust
  - peios/auditing/overview
---

When you ask peipkg to install `nginx`, you have not actually told it what to do. `nginx` needs other packages; those need others; some version of each has to be chosen; everything has to be installed in an order where a package's dependencies come before it. Turning the short request into that concrete, ordered plan is **resolution**, and it is the first thing every change command does.

## Resolution is a pure calculation

peipkg resolves from **metadata alone** — the package descriptions in the cached repository indexes and in installed packages' manifests. It does not download a single `.peipkg` to work out a plan. Downloading happens later, only once a plan is approved.

That makes resolution a pure calculation over three inputs — your request, the set of installed packages, and the set of available packages — and gives it a property worth relying on: it is **deterministic**. The same inputs always produce the same plan. The plan you inspect with `--dry-run` is exactly the plan that will execute; nothing is re-decided between previewing and applying.

If a request cannot be satisfied — a dependency that no repository can provide, two requirements that contradict — resolution **rejects it**, with an explanation, before anything is fetched or changed.

## The relationships between packages

A package's manifest declares how it relates to others. Four relationships drive resolution.

**Dependencies.** A package can require other packages, each by a version range. peipkg pulls every dependency into the plan, and their dependencies in turn, until the request is closed.

**Conflicts.** A package can declare that it cannot coexist with another. If a plan would put two conflicting packages on the system at once, resolution rejects it.

**Provides.** Several packages can advertise the same capability — a *virtual* name that is not itself a package. A dependency written against that name is satisfied by *any* package that provides it. This is how "needs a mail transport agent" can be met by whichever one you actually install.

**Replaces.** A package can declare that it supersedes another — the usual case being a rename, or a merge of two packages into one. Installing a package that `replaces` another causes the replaced package to be removed as part of the same plan.

## Choosing a version

When more than one version of a package could satisfy the plan, peipkg chooses by a fixed rule:

1. Prefer the **highest version** that satisfies every constraint on that package.
2. When two repositories offer the same version, prefer the one with the stronger (lower-numbered) **priority** — see [Repositories and trust](~peios/package-management/repositories-and-trust).

For an upgrade, the installed version anchors the search: peipkg looks for something newer and stays put if there is nothing newer to move to.

**Optional dependencies** are never chosen automatically. A package can suggest companions that are useful but not required; peipkg surfaces those as suggestions and leaves the decision to you. A plan only ever contains what is genuinely needed plus what you asked for.

## The plan

The output of resolution is the ordered list of operations you see at the `proceed?` prompt — installs, upgrades, downgrades, and removals, sequenced so every package's dependencies are in place before it.

A removal gets one extra step. peipkg first computes the **reverse-dependency closure** — everything that would be left needing a package you are removing — and either refuses the plan or, with `--cascade`, widens it to include them. That logic is covered in [Installing and removing packages](~peios/package-management/installing-and-removing).

Resolution is also **bounded**. A dependency graph cannot be crafted to make peipkg search forever; the resolver works under a hard cap and gives up cleanly rather than hanging if a graph is pathological.

## Elevated authorisation

Most of a plan is routine, and the single `proceed?` prompt covers it. But a plan can contain an action where a routine yes is not enough — where you should be made to look at *that specific action* and approve *it*, deliberately, on its own.

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

- **`--yes` does not satisfy it.** `--yes` skips the *routine* `proceed?` prompt; it has no effect on an elevated-authorisation question. The deliberate yes must be given deliberately.
- **It fails closed.** With no terminal to answer on — an unattended script, a pipeline — there is no answer, so the action is *not* authorised and the operation is cancelled. An elevated action never slips through for lack of someone to say no.

Each elevated action is presented and authorised on its own; approving one does not approve the next. And the authorising act is itself written to the [audit stream](~peios/auditing/overview) — the record shows not just what was done, but that it was specifically authorised and what was authorised.

If an elevated action is not one you want, the plan as a whole is the thing to reconsider: where the package is coming from, whether the repository priorities are right, whether the downgrade is really what you meant.
