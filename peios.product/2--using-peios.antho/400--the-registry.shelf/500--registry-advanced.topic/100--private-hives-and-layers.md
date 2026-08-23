---
title: Private hives and layers
type: concept
description: Private hives and layers give one caller its own view of the registry — the building block for sandboxing, with authorisation deferred to KACS.
related:
  - peios/registry-administration/lcs-and-sources
  - peios/registry-layers/layers
  - peios/registry-security/access-control
  - peios/registry-concepts/overview
---

Everything in the core topic describes one shared registry that every process sees the same way (subject to access control). **Private hives** and **private layers** relax that: they let a particular caller see a registry that differs from everyone else's — the building block for sandboxing and container-style isolation.

This is an advanced feature, and a partly forward-looking one. The registry defines how a private hive or layer participates in [resolution](~peios/registry-layers/layers); but *who* is allowed to see one is decided by a thread's credentials, and that credential model is part of KACS and not yet fully specified. Treat this page as the shape of the feature, not a how-to.

## Private hives

A **private hive** is a hive that is visible only to threads whose credentials carry a matching scope — an opaque identity that marks "you are allowed to see this hive". To everyone else it does not exist.

The powerful case is **shadowing**. A private hive can take the same name as a global one — `Machine\`, say — and for a thread that carries the scope, the private hive is what `Machine\` resolves to, not the global one. A sandboxed process can therefore be given an entirely separate `Machine\` while every other process continues to see the real one, with no change to the paths anyone uses. That is complete registry isolation without a parallel namespace: same paths, different contents, decided by who is asking.

## Private layers

A **private layer** is a [layer](~peios/registry-layers/layers) that is globally disabled — invisible in normal resolution — but attached to a specific thread's credentials. For that thread, and only that thread, the layer is treated as active and competes in the per-value contest at its precedence exactly like any other layer. Everyone else resolves as if it were not there.

This is the lighter-weight tool, for when you want a different *value* here and there rather than a whole separate hive:

- **Per-session overrides** — run one application with experimental settings without disturbing other sessions.
- **Testing** — inject configuration for one process without writing it into the shared registry.
- **Sandboxing** — give a confined process a slightly different view without standing up a private hive.

Private layers are **per thread, not per process**: because the attachment rides on a thread's credentials, different threads in the same process can carry different private layers (for instance, a service thread acting on behalf of a particular client). The number a thread can carry is bounded.

## Authorisation lives in KACS

The registry defines only the *resolution* behaviour — private hives are checked ahead of global ones, and a thread's private layers fold into its contests. The decision about whether a thread may join a scope or attach a layer belongs to KACS's credential model. One constraint is already clear and worth stating: attaching a layer that sits *above* others in precedence must be privileged, or an unprivileged process could attach an existing high-precedence policy layer to itself and gain a window onto configuration it should not see or influence. The isolation is only as strong as the rule that decides who may carry a scope or a private layer.

## Where to go next

For the resolution model these build on — precedence, recency, and the per-value contest — read [Layers](~peios/registry-layers/layers).

For where private hives are routed and served, read [LCS and sources](~peios/registry-administration/lcs-and-sources).
