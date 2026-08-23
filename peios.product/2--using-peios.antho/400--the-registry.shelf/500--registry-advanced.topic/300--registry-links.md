---
title: Registry links
type: concept
description: A key can be a symbolic link to another key — the one place the registry interprets a value — with layered targets and privileged creation.
related:
  - peios/registry-concepts/keys-values-and-types
  - peios/registry-layers/layers
  - peios/registry-security/access-control
  - peios/registry-concepts/overview
---

A registry key can be a **symbolic link** to another key. Open a link key by its path and the registry follows it through to the target, handing you a handle on the target key. Links let one part of the namespace point at another, the way a filesystem symlink does.

Links are an advanced feature with a small, sharp set of rules, and they are the **one exception** to a property the rest of the topic relies on.

## A link is a flag plus a target value

Two pieces make a link, and both are needed:

- The key is **marked** as a link when it is created. This is a fixed property of the key.
- The key's **default value**, of type `REG_LINK`, holds the **target path** — an absolute registry path the link points at.

When path resolution reaches a link key, the registry reads that target and continues resolving from there; the handle you get back refers to the target, not the link.

## The one place the registry reads a value

[Keys, values, and types](~peios/registry-concepts/keys-values-and-types) made a point of it: the registry stores a value's type and bytes but never interprets them. `REG_LINK` is the single exception. It is the one type the registry acts on itself — following it during path resolution — rather than handing it back untouched. Everything else remains opaque; links are the lone case where the store cares what a value *says*.

## Managing the link itself

Normally you want to follow a link. To operate on the link key *itself* — to change where it points or delete it — you open it with a flag that says "open the link, do not follow it". Without that flag every open lands on the target, which would make the link impossible to manage.

## Creating a link is privileged

Because a link silently redirects whoever opens it, creating one is restricted. It requires the `KEY_CREATE_LINK` right on the parent **and** a privileged caller (the system-trust privilege, or Administrator membership). A link is a small piece of trusted plumbing, not something an ordinary process gets to introduce into a path other callers will traverse.

There is one safety rule worth knowing: a link target is followed **literally**, and the `CurrentUser\` convenience alias is *not* expanded inside it. This stops a link from redirecting a privileged service that resolves `CurrentUser\` into the service's *own* user hive — a classic confused-deputy trap. Link targets route by their literal hive name. Resolution is also bounded by a hop limit, so a cycle of links fails rather than looping forever.

## Layers can redirect a link

The target is an ordinary [layered](~peios/registry-layers/layers) value — the link key's default value — so it plays by the same rules as any other value. A higher-precedence or more-recent layer can write a *different* `REG_LINK` target and redirect the link; remove that layer and the original target resurfaces, by the usual automatic revert. And if a layer writes a default value that is *not* a `REG_LINK` onto a key that is still flagged as a link, resolution through it fails until the offending layer is removed or overridden. The link's *identity* is fixed at creation; its *target* is just configuration, and configuration is layered.

## Where to go next

For the opaque-value rule this is the exception to, read [Keys, values, and types](~peios/registry-concepts/keys-values-and-types).

For how a layer can redirect or break a link, read [Layers](~peios/registry-layers/layers).
