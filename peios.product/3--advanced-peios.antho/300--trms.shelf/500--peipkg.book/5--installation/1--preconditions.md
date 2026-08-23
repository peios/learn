---
title: Preconditions
description: What must already be true before an install begins — the fetched file, the repository's trust state, the database and the plan.
---

An install begins with a package file already fetched, the repository it
came from with its trust state, the current database state, and the plan
that called for the install.

The following hold before the install proceeds:

1. The package's hash matches what the repository index recorded.
2. The package's signature, if present, verifies against the trust set
   scoped to its originating repository.
3. The package is not already installed at the same version and
   architecture in this root.
4. The package's architecture is the system's primary architecture or
   `noarch`.
5. The package's dependencies are satisfied by the installed set, by the
   plan in flight, or by both together.
6. No installed package conflicts with it.

A precondition failure aborts the install, and the transaction
containing it is rolled back.

## Verification before extraction

For a transaction containing several installs or upgrades, every
package's signature and index-hash verification completes before any
package's payload is extracted.

> [!NOTE]
> This prevents a class of multi-package attack: package A is verified,
> extracted, and its contents then influence the verification or
> extraction of package B — A installs a tool B's extraction invokes, or
> A creates a directory whose descriptor decides where B's files land.
> Verifying everything first means extraction operates on a known-good
> set of payloads.

Within a single root, the guarantee holds: every package is provided and
verified before the first is materialised.

Across roots it does not. A cross-root transaction prepares and applies
each root in sequence, so one root's payload is on disk in its final
location before the next root's packages have been fetched or verified.
