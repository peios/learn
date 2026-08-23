---
title: Threats Out of Scope
description: What the package manager explicitly does not defend against, and where each of those concerns is addressed instead.
---

The following are explicitly outside what the package manager defends
against. Each is a real concern; each is addressed elsewhere.

**Compromise of an installing operator's identity.** peipkg runs with
the operator's authority (§13.1). If that identity is compromised, no
format-level defence helps. The kernel's own audit and recovery
mechanisms apply.

**Side-channel attacks on installed binaries.** Speculative-execution,
cache-timing, and similar attacks against installed software are the
kernel's concern and the software's, not the package format's.

**Physical attacks on storage.** A physically compromised disk can have
its package database or installed files altered offline. Hash
verification at use time — outside the package manager — is the
appropriate defence.

**Compromise of the build farm.** A compromised farm can sign malicious
packages with trusted keys. Detection requires independent
reproducible-build verification (§12.7).

The build farm identifier recorded in each manifest can be constrained
per repository as defence in depth — refusing packages from a farm not
on a configured allowlist. That is not implemented, and it would protect
only against a stale farm whose key was rotated but whose identifier is
still recognised, or against an attacker who obtained a key without the
farm's operational identity. It is not a format-level guarantee.

**Network-level censorship or denial of service** preventing package
fetching. An operational concern.

> [!NOTE]
> These exclusions are honest acknowledgements rather than weaknesses to
> dismiss. What they have in common is that each sits either below the
> package manager — where the kernel is the right layer — or above it,
> where the operator's judgement about what to trust is the only thing
> that can help.
