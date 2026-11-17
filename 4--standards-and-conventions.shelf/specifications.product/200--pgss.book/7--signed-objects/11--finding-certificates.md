---
title: Finding Certificates
description: How a verifier finds an intermediary that a bundle names but
  does not carry, by its hash in a directory packages install into, and
  why the directory needs no protection.
---

A bundle that stops short names a certificate it does not carry (§7.8).
A verifier finds it by its object hash.

## Top-levels

If the hash is that of an enabled top-level, the verifier uses the
top-level from the trust store (§7.10).

## Intermediaries

Otherwise the verifier reads the file named by the hash in
`/usr/share/pso/intermediate/`. A package that ships intermediaries
installs each there, in a file named by its object hash (§7.4).

The `/usr` in question is that of the party on whose behalf the
verifier is working: the process that asked, or the process loading the
file. Where the verifier works for the system itself, it is the
system's own.

A verifier MUST do all of the following:

- Read only a regular file, and follow no path to anything else.
- Read no more than 65,535 bytes.
- Check that the content's object hash is the hash it was looking for.
- Treat the certificate, once read, exactly as if the bundle had carried
  it.

A verifier MAY remember a certificate it has verified, by its hash. What
it remembers MUST NOT delay a change to the trust store: a revocation or
a distrust entry applies to every verification after it is accepted.

> [!NOTE]
> The directory is whatever the asking process has as its `/usr`, and
> a process can arrange for that to be anything. This is safe because
> a certificate found there proves itself: its hash has to match the
> one a signed object named, and it still has to chain to an enabled
> top-level. Placing a file there gains nothing. That is also why a
> system with many closures needs no central list of intermediaries:
> each closure carries the ones its own programs use.

## When nothing is found

If the named certificate is in none of these places, the chain cannot
be completed. A verifier reports this as its own result, not as an
invalid chain (§7.14): a file whose intermediary is not installed has
not been altered.
