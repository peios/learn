---
title: Binary Format
description: The PEIOSEAL v1 sealed secret — its 52-byte header, the Argon2id parameters and salt it records, the AES-256-GCM nonce, and the ciphertext and tag after it.
---

A **sealed secret** is a secret encrypted under a key derived from a
passphrase, in a self-describing blob: it records everything needed to
open it except the passphrase. The certificate authority keeps its
private keys in sealed secrets, and so do Peios Signed Objects' key
files.

This chapter specifies version 1, identified by the magic `PEIOSEAL`. It
says nothing of what the secret is: a caller seals whatever bytes it
holds and gives them meaning itself.

Unlike the rest of this document, every multi-byte integer in a sealed
secret is **big-endian**.

## Layout

| Offset | Size | Field | Value |
|---:|---:|---|---|
| 0 | 8 | `magic` | ASCII `PEIOSEAL` |
| 8 | 1 | `version` | `1` |
| 9 | 1 | `kdf` | `1`, Argon2id version 0x13 |
| 10 | 4 | `memory` | Argon2 memory in KiB, uint32 |
| 14 | 4 | `passes` | Argon2 passes, uint32 |
| 18 | 4 | `lanes` | Argon2 lanes, uint32 |
| 22 | 1 | `salt_len` | `16` |
| 23 | 16 | `salt` | Argon2 salt |
| 39 | 1 | `cipher` | `1`, AES-256-GCM |
| 40 | 12 | `nonce` | AES-GCM nonce |
| 52 | n | `ciphertext` | The secret, encrypted; as long as the secret |
| 52 + n | 16 | `tag` | The AES-GCM authentication tag |

The first 52 bytes are the **header**. A sealed secret is at least 68
bytes long: the header and the tag around an empty ciphertext, which is
valid.

The `kdf` and `cipher` enumerations are closed for version 1. A value
other than `1` in either is not a version 1 sealed secret.

> [!NOTE]
> The header's fields are laid out so that a later version could add
> another key derivation, such as PBKDF2 for a FIPS-validated system,
> as a new `kdf` value. A version 1 reader refuses it rather than
> guessing.
