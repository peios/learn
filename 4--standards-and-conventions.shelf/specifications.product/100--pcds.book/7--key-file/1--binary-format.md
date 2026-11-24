---
title: Binary Format
description: The PEIOSKEY v1 key file — its 14-byte header, the algorithm, protection and flags it records, the public key in the clear, and the private key after it.
---

A **key file** holds one asymmetric key pair: the public key in the
clear, so that a program can tell which key a file holds without opening
it, and the private key, either sealed under a passphrase or kept in the
clear for storage that access control protects. The certificate
authority keeps every CA key in a key file, and exports keys only as
sealed key files.

This chapter specifies version 1, identified by the magic `PEIOSKEY`.

Unlike most of this document, every multi-byte integer in a key file is
**big-endian**.

## Layout

| Offset | Size | Field | Value |
|---:|---:|---|---|
| 0 | 8 | `magic` | ASCII `PEIOSKEY` |
| 8 | 1 | `version` | `1` |
| 9 | 1 | `algorithm` | The key's algorithm, §7.2 |
| 10 | 1 | `protection` | `1`, passphrase; `2`, access control |
| 11 | 1 | `flags` | Bit 0, not exportable; the other bits zero |
| 12 | 2 | `public_len` | Length of `public_key`, uint16 |
| 14 | `public_len` | `public_key` | The public key, a DER `SubjectPublicKeyInfo` |
| 14 + `public_len` | rest | `private_key` | The private key, as `protection` says |

The first 14 bytes are the **header**. `public_key` and `private_key`
are each at least one byte long, and `private_key` runs to the end of
the file.

`private_key` depends on `protection`:

- **`1`, passphrase:** a sealed secret (§6) of the private key's
  PKCS #8 encoding, sealed under the key's passphrase.
- **`2`, access control:** the private key's PKCS #8 encoding itself.
  Only the access control of the storage that holds the file keeps it
  secret.

The **not exportable** flag asks the program that holds the key never
to release it, even to a caller that may otherwise read it. It is
meaningful only with access-control protection: whoever has a sealed key
file and its passphrase already has the key.

The `algorithm` and `protection` enumerations and the `flags` bits are
closed for version 1. A value this chapter doesn't define is not a
version 1 key file.

> [!NOTE]
> Nothing before `private_key` is secret: a CA's certificate carries the
> same public key. Nor is it authenticated, even in a sealed key file,
> whose sealed secret covers only the private key. That is why a reader
> checks the private key against the recorded public key once it has
> opened it (§7.3).
