---
title: Opening
description: How a reader opens a sealed secret — the checks before any key is derived, the bounds on recorded parameters, and why every later failure is one error.
---

A reader MUST make these checks, in this order, before it derives a key,
and MUST treat a sealed secret that fails any of them as malformed:

1. It is at least 68 bytes long, and its first 8 bytes are `PEIOSEAL`.
2. `version` is `1`, `kdf` is `1`, and `cipher` is `1`.
3. `salt_len` is `16`.
4. `memory` is at most 1,048,576 KiB, `passes` is from 1 through 16,
   and `lanes` is from 1 through 16.

A reader MUST also treat as malformed any parameters its Argon2
implementation refuses, such as `memory` below 8 KiB for each lane.

The reader then derives the key as §6.2 does, with the recorded
parameters and salt, and decrypts with the recorded nonce and the header
as associated data.

A reader MUST report a failure to decrypt as one error, meaning that the
passphrase is wrong or the sealed secret has been altered. It MUST NOT
say which.

> [!NOTE]
> The bounds exist because the header is authenticated only after the
> derivation has run. Without them, a hostile sealed secret could make
> its reader spend gigabytes of memory or hours of work before failing.
> They are wide enough that a producer can raise its parameters a long
> way before it reaches them.
