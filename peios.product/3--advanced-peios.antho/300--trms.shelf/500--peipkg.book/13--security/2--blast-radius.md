---
title: Blast Radius
description: With no standing privileged identity there is nothing to confine and nothing to compromise — and what peipkg therefore does not do.
---

Because peipkg holds no principal of its own, there is no standing
privileged identity to confine and no privileged process to compromise.
The authority exercised during an install is the caller's, and only for
the duration of that invocation.

The blast radius of installing a malicious or defective package is
therefore bounded, precisely, by the authority of the operator who
installed it: **a malicious package can do nothing the operator could
not already do directly.**

That makes the trust decision — which repositories an operator
configures, and which packages an operator with broad authority chooses
to install — the operative security boundary. Signature verification and
the repository trust model exist to inform that decision. They do not
substitute for it.

## What peipkg does not do

peipkg needs write access to the payload destinations and network access
to fetch from configured repositories, and nothing beyond that.

- It performs no `kexec`.
- It loads no kernel modules. The `depmod` side effect rebuilds a module
  dependency map; it does not load anything.
- It loads no BPF programs.
- It writes no registry state. Its bookkeeping is a private store, and
  the database schema says so in as many words.

The one thing that reaches outside its own state is a side effect, and
that is a fixed absolute path, with a cleared environment, from a closed
set of three (§11.2).

> [!NOTE]
> peipkg has its own thing it calls a registry: the table recording
> which named roots exist. That is a table inside the private store, not
> the system registry, and the claim above is about the latter.
