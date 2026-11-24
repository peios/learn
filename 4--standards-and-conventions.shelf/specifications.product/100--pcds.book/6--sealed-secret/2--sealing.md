---
title: Sealing
description: How a secret is sealed — a fresh salt and nonce, Argon2id deriving a 32-byte key, and AES-256-GCM with the whole header as associated data.
---

To seal a secret under a passphrase, a producer:

1. Draws a fresh 16-byte `salt` and a fresh 12-byte `nonce` from a
   cryptographically secure random number generator.
2. Chooses Argon2 parameters, `memory`, `passes` and `lanes`, within the
   bounds of §6.3.
3. Writes the header of §6.1 with those values.
4. Derives a 32-byte key with Argon2id, version 0x13 (RFC 9106), from
   the passphrase's bytes as the password and `salt` as the salt, with no
   secret value and no associated data.
5. Encrypts the secret with AES-256-GCM under that key and `nonce`, with
   the whole 52-byte header as the associated data, and appends the
   ciphertext and the 16-byte tag to the header.

A producer MUST draw a new salt and a new nonce for every seal, including
when it seals the same secret under the same passphrase again.

A producer SHOULD use 65,536 KiB of memory, 3 passes and 4 lanes, the
second recommended option of RFC 9106 §4, unless it has measured that
the machine that opens the secret can afford more.

The passphrase's bytes are used as they are given. Turning typed text
into those bytes is §6.4's.

> [!NOTE]
> The header is the cipher's associated data, so changing a recorded
> parameter, the salt or the nonce makes the tag fail. Lowering
> `memory` to make guessing cheaper therefore can't succeed without the
> passphrase. A fresh salt makes a fresh key on every seal, which is
> what makes a random 12-byte nonce safe: no key ever sees two nonces.
