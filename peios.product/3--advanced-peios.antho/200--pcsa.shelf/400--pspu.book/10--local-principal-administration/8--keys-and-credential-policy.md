---
title: Keys and Credential Policy
description: A principal's SSH public keys, and its credential policy — which credentials it may sign in with.
---

A principal's **credential policy** says which credentials it may sign
in with. Its **SSH public keys** are what it may sign in with by key
(PGSS §2.D). The two are separate on purpose: adding a key does not let
anyone sign in with it until the policy says keys are accepted, so
enrolling a key and allowing key sign-in are two decisions, and neither
happens as a side effect of the other.

## Credential policies

| Value | Policy | Signs in with |
|---|---|---|
| `0` | `Denied` | nothing: every sign-in is refused |
| `1` | `Password` | its password |
| `2` | `SshPublicKey` | one of its SSH keys |
| `3` | `PasswordOrKey` | either |
| `4` | `NoCredential` | nothing collected (§10.5, `Add`) |

The enumeration is closed (§10.4). A store daemon MUST refuse a value it
does not know.

## KeyList

`msg_type` = `0x0011`. Body: `name`. Answered with `Keys`.

## Keys

`msg_type` = `0x8008`. The principal's credential policy and keys:

| Field | Encoding |
|---|---|
| `policy` | `u8` |
| `keys` | array of at most 32 length-framed keys |

A key:

| Field | Encoding |
|---|---|
| `id` | byte string, 16 bytes: the store daemon's, never all zero |
| `fingerprint` | string, 128 bytes: as `ssh-keygen -l` writes one |
| `label` | string, 128 bytes |
| `created` | `u64`: seconds since the Unix epoch |

`KeyList` is the one request that answers the credential policy, so a
client reading a principal's policy sends it.

## KeyAdd

`msg_type` = `0x0012`. Enrols an SSH public key. Answered with `Done`.

| Field | Encoding |
|---|---|
| `name` | string, 256 bytes |
| `public_key` | string, 16384 bytes: one line of an OpenSSH `authorized_keys` file |
| `label` | string, 128 bytes, no control characters |

A store daemon MUST refuse, as `Invalid`, a key it cannot read or does
not support, a key the principal already has, a 33rd key, and a label
too long or carrying a control character. It does not change the policy.

## KeyRemove

`msg_type` = `0x0013`. Body: `name`, then `id`, a byte string of 16
bytes. Removes the key. Answered with `Done`, or `NotFound` for an `id`
the principal has no key by.

## CredentialPolicy

`msg_type` = `0x0014`. Body: `name`, then `policy`, a `u8`. Sets the
principal's credential policy. Answered with `Done`.
