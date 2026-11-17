---
title: Conformance
description: The obligations of a store keeper toward the kernel, gathered
  in one place, with what the kernel guarantees in return and what a
  store keeper is free to do.
---

## A conforming store keeper

- Writes the store image whenever the store changes, and replaces it in
  one step (§6.3).
- Puts in the image, and adds through ktrust, only top-level
  certificates, revocations, and distrust entries (§6.3, §6.5).
- Never tells the kernel whether a top-level is rooted, and relies on
  the kernel's own decision (§6.3).
- Reconciles the kernel's store with the trust store each time it
  attaches (§6.5).
- Starts a listing again if the generation changes during it, where it
  needs a consistent view (§6.5).
- Lists the seen certificates again after an Overflow (§6.6).
- Writes zero in every reserved field (§6.7).

## What the kernel guarantees

- It reads the image once, before it runs its first program, and never
  again (§6.3).
- It verifies every signature it holds a key for, and rejects an object
  that fails (§6.3, §6.5).
- It never removes a revocation (§6.5).
- It keeps the store when a store keeper detaches (§6.4).
- It records every certificate it verifies, from boot, up to the limit
  of §6.A (§6.5).

## What conformance does not require

Conformance does not require a store keeper to stay attached, to read
notifications, or to use the record of seen certificates at all. It
does not say how a store keeper obtains an administrator's approval,
which is PGSS §7.10, or how the image reaches the filesystem the kernel
boots from.
