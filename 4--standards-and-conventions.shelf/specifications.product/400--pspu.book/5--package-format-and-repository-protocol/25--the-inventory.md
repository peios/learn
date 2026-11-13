---
title: The Inventory
description: The line format at the top of a closure that records its packages and what wants each, its brackets, its order, and how a closure's identity comes from it.
---

A closure's **inventory**, `/usr/inventory` when it is mounted, records the
closure's identity and its packages, and why each is there.

## Form

```text
closure sha256:9c41…
org.openssl.libssl@3.5.8-1?arch=x86_64 sha256:… [se.curl.curl libssl.so.3]
se.curl.curl@8.22.0-1?arch=x86_64 sha256:… [* #stable >=8.22]
```

The first line is `closure`, a space, and the closure's identity. Each other
line is one package: its full ID, a space, its identity, then a space and a
**bracket** for each thing that wants it.

A bracket is `[`, then tokens separated by single spaces, then `]`:

1. **Who wants it:** `*` for a request of the closure itself, or the name of
   a package in the closure.
2. **What it asked for**, if it asked for a capability rather than the
   package by name: the capability (§5.4).
3. **Where from**, for a request that named an index or channel: `#` and its
   name (§5.29). Only a `*` request names one.
4. **Which versions would do:** one token for each expression of the
   constraint, its operator and its version with no space between, such as
   `>=8.22`; none for any version.

A capability never starts with an operator, and a constraint token always
does, so the two can't be confused. No package can be named `*`.

## What wants a package

A package is wanted by every request it satisfies, and by every dependency
and requirement of another package in the closure that it satisfies (§5.21).
So the brackets are worked out from the packages and the requests alone,
however the closure was reached. A requirement's bracket always names its
capability, even where the capability is the package's own name.

Every package of a closure MUST be wanted by something, and every request
MUST be satisfied by a package of it. A dependency or requirement need not
be satisfied: a closure of exactly the packages given doesn't check what
they need.

## Order

Lines are sorted by the bytes of the full ID. Brackets are sorted by who
wants the package, `*` first and then by name, then by capability, none
first, then by index, none first, then by the constraint's tokens. A bracket
that would be written twice is written once.

## Identity

The closure's identity is the identity (§5.9) of every line after the first.
A consumer MUST refuse an inventory whose first line doesn't name that
identity, or that isn't in this form.
