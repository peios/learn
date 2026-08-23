---
title: Terminology
description: Terms this manual borrows unchanged from PSPU §5, and the ones it adds for itself.
---

Terms defined in PSPU §5.2 — package, manifest, files manifest, payload,
repository, descriptor, index, virtual name, role, claim, holder,
installation root, trust anchor — carry the same meaning here and are
not redefined.

Terms specific to the implementation:

- **Transaction** — the atomic unit of work. Every install, upgrade,
  uninstall, grant, and revoke executes within one, even when it
  contains a single operation.

- **Plan** — the resolver's output: an ordered list of operations that,
  applied to the installed set, satisfies the request. A plan is
  computed entirely from index data, before anything is fetched.

- **Goal** (or *target*) — one requested operation the operator named:
  install this, upgrade that, remove the other.

- **Candidate** — an available package, drawn from a repository index,
  that the resolver may select.

- **World** — the resolver's working model, keyed by (name, root): every
  installed package plus every operation in flight.

- **Journal** — the record of a transaction's intent, stored as rows in
  the package database. It carries the *backup map*: for each displaced
  file, the sibling path its original was renamed to.

- **Staged file** — a file written to a temporary sibling of its
  destination, within the same directory, before the transaction
  commits. Nothing appears at a final install path until the apply
  phase.

- **Backup** — a displaced original, renamed aside within its own
  directory. Backups cost no additional disk space and are produced by a
  single rename.

- **Authorization** — a resolver output demanding an explicit,
  action-specific act from the operator before the plan may be applied.
  Distinct from a **notice**, which is informational and never blocks.

- **Adoption** — recording an existing unowned file as owned by an
  installing package, without rewriting it, when its content already
  matches what would have been installed.

- **Side effect** — one of the three standard maintenance operations a
  package may declare (PSPU §5.24).

- **Recipe** — a `pekit.toml` file plus its build script: the input to
  the producer toolchain describing how to turn an upstream source tree
  into one or more packages.

- **Lock** (in composition) — the pinned, resolved closure an image
  composition records, so that the same inputs produce the same image.
  Not to be confused with the transaction lock, which is a mutual
  exclusion primitive.
