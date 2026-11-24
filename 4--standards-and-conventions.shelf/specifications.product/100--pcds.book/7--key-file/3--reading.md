---
title: Reading
description: The checks a reader makes on a key file's header, and how it opens the private key and confirms that it matches the recorded public key.
---

A reader MUST treat a key file that fails any of these checks as
malformed:

1. It is at least 14 bytes long, and its first 8 bytes are `PEIOSKEY`.
2. `version` is `1`.
3. `algorithm` is a value §7.2 defines.
4. `protection` is `1` or `2`.
5. No bit of `flags` other than bit 0 is set, and bit 0 is clear if
   `protection` is `1`.
6. `public_len` is not zero, and at least one byte follows `public_key`.
7. `public_key` is the canonical DER encoding of a key of `algorithm`.

A reader can describe a key from these fields alone: its algorithm, its
public key, how it is protected, and whether it may be exported.

To open the private key, a reader takes `private_key` as it is, with
access-control protection, or opens it as a sealed secret under the
key's passphrase (§6.3), with passphrase protection. It then parses the
PKCS #8 encoding, and MUST refuse the key unless it is a key of
`algorithm` whose public key is exactly `public_key`.

A program that holds a key file whose not-exportable flag is set MUST
NOT release the private key, sealed or in the clear.

> [!NOTE]
> The last check is what makes the unauthenticated header safe. Someone
> who alters `public_key` or `algorithm` can make a key file describe
> another key, but not make it open as one: the private key no longer
> matches, and the reader refuses it.
