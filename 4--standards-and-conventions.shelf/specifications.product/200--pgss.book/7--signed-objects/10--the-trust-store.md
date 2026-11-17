---
title: The Trust Store
description: The directories that hold top-levels, revocations, and
  distrust entries, which top-levels a store keeper enables, how a
  package's self-signed top-level is quarantined, and how approval is
  recorded as a link.
---

The **trust store** is the part of a system that says which top-levels
it trusts. A verifier accepts a top-level only if the trust store
enables it. A top-level found anywhere else, including in a bundle, is
not enabled.

## Directories

The store is read from two trees.

| Directory | Written by | Holds |
|---|---|---|
| `/usr/share/pso/toplevel/` | Packages | Top-levels that packages ship |
| `/usr/share/pso/revocation/` | Packages | Revocations that packages ship |
| `/lcl/policy/pso/toplevel/` | The store keeper | Top-levels the administrator trusts |
| `/lcl/policy/pso/revocation/` | The store keeper | Revocations the store keeper has accepted |
| `/lcl/policy/pso/distrust/` | The store keeper | Distrust entries (§7.13) |

`/usr` here is the system's own, the closure a system runs as (PSPU
§5.27), and never the `/usr` of another closure.

Each entry is one object in a file of its own. A top-level or a
revocation is named by its object hash, and a distrust entry by the hash
it distrusts, in the form §7.4 gives. A store keeper MUST ignore an
entry whose content does not match its name.

## Which top-levels are enabled

A store keeper enables a top-level in exactly these cases:

- It is in `/usr/share/pso/toplevel/`, its `issuer` is the key hash of a
  root the system's verifier holds, and its signature verifies under
  that root.
- It is in `/lcl/policy/pso/toplevel/`.

A top-level in `/usr/share/pso/toplevel/` that a root did not sign is
**quarantined**. It is present and it is not enabled.

> [!NOTE]
> `/usr` is written by packages. If a self-signed top-level were
> enabled by being there, installing any package would be enough to
> give its publisher a trust anchor. A root-signed top-level needs no
> such care, because the root's signature already vouches for what it
> claims.

## Approval

An entry in `/lcl/policy/pso/toplevel/` is one of two things:

- **A file.** A top-level the administrator supplied directly.
- **A symbolic link** to the entry of the same name in
  `/usr/share/pso/toplevel/`. This is the administrator's approval of a
  quarantined top-level.

A store keeper MUST record an approval as a link and MUST NOT copy the
certificate. A link whose target is absent enables nothing.

A store keeper MUST resolve a link against the root of the system whose
store it is reading, which is not always the system it is running on.

> [!NOTE]
> The link leaves the package as the owner of the certificate. If the
> package later withdraws its top-level, the link dangles and the
> top-level stops being enabled, with no action from the administrator.
> A copy would outlive the package's own decision. A replacement
> certificate has a different hash, so it arrives quarantined and is
> approved on its own merits.

A store keeper MUST obtain the administrator's approval before it adds
an entry to `/lcl/policy/pso/toplevel/`, and MUST show the certificate's
name and every warrant it holds before the approval is given. How
approval is obtained is the store keeper's.

## What enabling means

Enabling a top-level trusts its holder with every warrant the
certificate states. This chapter gives a store keeper no way to enable a
top-level for some of its warrants and not others.

For a root-signed top-level, the root vouches for those warrants. For
any other, nothing does: a self-signed top-level states whatever its
maker wrote. That difference is why §7.14 reports the two apart.

## Access

The directories under `/lcl/policy/pso/` grant authority. A system MUST
restrict writing to them to its store keeper.
