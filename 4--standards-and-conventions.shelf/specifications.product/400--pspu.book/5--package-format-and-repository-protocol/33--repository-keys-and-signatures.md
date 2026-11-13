---
title: Repository Keys and Signatures
description: How a repository's pointer file is signed with ML-DSA-65, the context, the form of its keys, and what a signature vouches for.
---

A repository is signed with an ML-DSA-65 key of its own. Publishing a
repository MUST sign its pointer file.

## The signature

`repository.sig` is the ML-DSA-65 signature of the pointer file's bytes,
made in the context `ppk repository`, encoded as ML-DSA encodes a
signature. The context keeps a signature over a pointer file from being a
signature over anything else the key signs. A publisher SHOULD sign
deterministically, and MUST check the signature it made before writing it.

## Keys

A private key is a PKCS #8 file in PEM, as OpenSSL writes one for
ML-DSA-65, holding the key's seed. Only the seed is needed; where the file
holds the expanded key too, it MUST be the seed's.

A public key is written `ml-dsa-65:` and the base64 of the key's encoding,
to go in a machine's configuration of the repository (§5.35).

A private key MUST NOT be kept in the repository, or anywhere it is
published.

## What it vouches for

A machine checks a repository's signature only if its configuration of the
repository gives a public key (§5.35), and only when it fetches through that
configuration. Then the pointer file MUST be signed with that key, and a
package is taken from the repository only if the catalog the pointer file
names lists it, at the identity the catalog gives (§5.29). Every tree node,
manifest and blob is reached through hashes from the pointer file, so for a
repository used that way the signature vouches for all of them.

Reading the same directory as a plain artifact directory, without its
configuration, checks none of this: its refs are taken as they are (§5.26).

A repository without a key in the machine's configuration, such as a medium's
store or a local directory, is trusted because whoever configured it
supplied it.

## A future scheme

This version signs with one key per repository. A later version MAY sign the
pointer file under a chain of certificates instead; the signature stays
detached, so only the pointer file's signature and the machine's
configuration change, and no hash does.
