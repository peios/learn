---
title: Scope and Roles
description: What the Trust Store Interface specifies, the store image the
  kernel reads at boot and the ktrust channel a store keeper changes the
  store through, and what the kernel takes on the store keeper's word.
---

This chapter specifies the **Trust Store Interface**: how the Peios
kernel is given the trust store of PGSS §7.10, and how that store is
changed while the system runs. The channel is called **ktrust**.

The kernel verifies signed objects (PGSS §7) for its own purposes and on
behalf of any process that asks. To do so it has to know which
top-levels are enabled, which revocations apply, and what the
administrator distrusts. It does not read the trust store's directories.
It holds the store in memory, filled from two sources that this chapter
defines.

Two roles participate.

| Role | Obligation |
|---|---|
| Kernel | Holds the store, validates everything it is given, and applies it to every verification. There is one kernel. |
| Store keeper | The store keeper of PGSS §7.1. Composes the store image and tells the kernel of every later change. Every rule on what is sent binds the store keeper. |

The store keeper role is publicly implementable. The kernel recognizes
a store keeper by privilege and by a warrant (§6.4), not by what
program it is.

This chapter covers:

- the store image, which the kernel reads before it runs any program
  (§6.3)
- the device, and how a store keeper attaches to it (§6.4)
- the operations a store keeper issues, and their results (§6.5)
- the notifications the kernel sends (§6.6)

This chapter does not cover:

- The objects the store holds, and how a chain is verified. Those are
  PGSS §7.
- The trust store's directories, and the approvals a store keeper
  obtains. Those are PGSS §7.10.
- The system call by which a process asks the kernel to verify a file,
  and what the kernel does with a result at exec. Those are the Peios
  Kernel TRM's.
- The events the kernel emits about verification. Those are documented
  by evman.

## What the kernel establishes for itself

The kernel checks that every object it is given is well formed, and
verifies every signature it holds a key for. It decides for itself
whether a top-level is vouched for by a root (§6.3). It decides for
itself, at each verification, whether a revocation applies to the chain
in front of it.

## What the kernel takes on trust

The kernel cannot tell whether an administrator approved anything. It
believes a store keeper on two points:

- that a top-level no root signed is one the administrator trusts
- that a distrust entry being removed is one the administrator agreed
  to remove

A store keeper is therefore inside the trusted computing base for
exactly those two decisions, and for nothing a signature can settle.
That is why attaching is restricted as §6.4 describes.
