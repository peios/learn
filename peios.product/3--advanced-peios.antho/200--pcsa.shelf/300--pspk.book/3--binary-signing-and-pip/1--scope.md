---
title: Scope and Roles
description: How a binary is signed so the Peios kernel will accept it, who the signer and verifier are, and why signing is a contract rather than an implementation detail.
---

This chapter specifies how a binary is signed so that the Peios kernel
will accept it, and what the trust level a signature confers means.

Two roles participate.

The **signer** is a userspace program holding a private key. It
computes a content hash over a file, signs it, and attaches the
signature to that file. The signer role is publicly implementable: a
third party building software for Peios, or an organisation operating
its own trust tier, MUST be able to produce an acceptable signature
from this chapter alone.

The **verifier** is the Peios kernel. It carries public keys, checks
signatures at execution and at library load, and derives a process's
Process Integrity Protection identity from whichever key verified. The
verifier role is not publicly implementable and is not specified here;
this chapter constrains it only where the signer needs guarantees
about what it will do.

This chapter covers:

- the signature blob's encoding
- where a signature is stored, and the order in which storage
  locations are consulted
- exactly which bytes are covered by the signature
- the signature algorithm, its parameters, and the absence of domain
  separation
- how a key is selected during verification, and how a trust tier
  follows from it
- the meaning of a PIP identity, and what a signer is asserting by
  requesting one
- the guarantees a signer may rely on, and the ones it may not

This chapter does not cover:

- how the kernel parses, hashes, or verifies — described in the Peios
  Kernel TRM
- how PIP is enforced between processes or against objects — likewise
  the TRM's concern
- key generation, custody, rotation, or distribution policy
- the process mitigations that compose with PIP, which are set by a
  process launcher and are unrelated to signing

## Why signing is a contract and not an implementation detail

A binary's trust level is not something a process can request. There is
no runtime interface that confers PIP, no inherited grant from a
parent, and no flag at process creation. The **only** input is the
signature on the file being executed, and the only authority is the
key that verifies it.

That makes the signature the entire boundary. A signer that produces
a byte-for-byte correct blob over the correct bytes obtains a trust
tier; one that gets any of it wrong obtains none, silently, because an
unverifiable binary executes with no protection rather than failing to
execute. There is no error to observe and no diagnostic to read.

A specification is therefore the only thing standing between a signer
and a silent, total loss of the property it was trying to obtain.

## What the kernel establishes for itself

The verifier trusts nothing in the artifact except the signature's
arithmetic.

The trust tier is **not** carried in the signature, the file, or any
metadata a signer controls. It is a property of the key that verified,
looked up in a table compiled into the kernel image. A signer cannot
encode, request, or influence the tier it receives; presenting a
signature made with a key the kernel does not carry is
indistinguishable from presenting no signature at all.

The signature covers the file's content, and the verifier re-derives
the content hash itself over a stable size snapshot rather than
trusting any length or digest recorded in the artifact.

A verified file is pinned against in-place modification for as long as
its inode lives, so a signer MUST NOT assume it can update signed
content in place. Replacement by a new inode is the only supported
update path.

## Relationship to PGSS

Binary signing is not a conformance requirement in the sense PGSS
defines. A system that verifies no signatures, or verifies them
against different keys, is still Peios; PIP is additive protection
rather than a property every Peios system exhibits.

It is specified here because the contract is public even so. A third
party that wants its software to run at a trust tier — or that wants
to operate a tier of its own — needs the format written down exactly,
and needs to know which of the verifier's behaviours it may depend on.
