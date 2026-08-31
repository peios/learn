---
title: peipkg-compose
description: Assembling an image without installing anything onto the building machine, sharing peipkg's resolver and archive reader.
---

`peipkg-compose` builds a filesystem tree from packages, without
installing anything onto the machine doing the building. It is how an
image is assembled.

It shares peipkg's resolver, its archive reader, its claim logic, and
its package database schema. What it does not share is the runtime: it
has no transaction journal to recover, no lock to hold against a running
system, and no operator sitting in front of it.

Composition runs in two phases, and they can be run separately.

**Resolve** performs the full repository trust ceremony, resolves the
requested package set against the configured repositories' indexes, and
writes a **lock**: the pinned closure, with each package's URL, hash and
declared sizes, and the trust state of every repository it draws from.

**Build** reads the lock, fetches each package, checks its bytes against
the hash the lock recorded, verifies its signature against the trust
state the lock carries for its source, and assembles the tree —
extracting payload, materialising claim links, and seeding a package
database so that the resulting image knows what it contains.

Chapter 10 describes composition in detail, including what it does not
do that an installed system's peipkg would.
