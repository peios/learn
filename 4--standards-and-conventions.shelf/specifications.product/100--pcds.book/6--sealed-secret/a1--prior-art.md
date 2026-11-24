---
title: Prior Art
description: Where the sealed secret sits against PKCS #8's encrypted keys and age's passphrase recipients, and which of their choices it keeps.
---

## Encrypted PKCS #8

PKCS #8 (RFC 5958) encrypts a private key under a passphrase with a key
derivation and cipher named by ASN.1 algorithm identifiers, usually
PBKDF2 and AES-CBC. A sealed secret keeps the idea of recording the
derivation's parameters with the ciphertext, and drops ASN.1 for a fixed
layout. It uses a memory-hard derivation, Argon2id, and an authenticated
cipher whose associated data covers the parameters, which PKCS #8's
common profiles do not.

## The age file encryption tool

age's scrypt recipient seals a file key under a passphrase, records its
work factor, and bounds it on reading so that a hostile file can't
demand unbounded work. A sealed secret does the same with Argon2id, and
bounds memory, passes and lanes separately.

## Design influences

**One error for every failure to open.** A reader that said whether the
passphrase or the ciphertext was wrong would tell an attacker which.

**The secret is the caller's.** A sealed secret encrypts bytes and says
nothing of what they are, so each format that uses it, the certificate
authority's key files and PSO's, keeps its own envelope and its own
checks on what it unseals.
