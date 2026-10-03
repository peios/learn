---
title: Claims
description: Setting and removing a principal's claims — the typed attributes conditional ACEs are evaluated against.
---

A principal's **claims** are named, typed attributes that the authority
puts on the tokens it mints for them, and that conditional ACEs are
evaluated against (PCDS §5.9). `Principal` carries them (§10.5).

## SetClaim

`msg_type` = `0x000f`. Sets a claim, replacing one of the same name.
Answered with `Done`.

| Field | Encoding |
|---|---|
| `name` | string, 256 bytes: the principal |
| `claim` | one claim (§10.4) |

Claim names match without regard to case. A store daemon MUST refuse, as
`Invalid`, a claim PSI could not carry to the authority (§2.13): a name
empty or longer than 255 bytes or containing a NUL, a flag or value type
it does not recognise, more than 64 values, or a string or octet value
longer than 1024 bytes. It MUST refuse a 65th claim on one principal.

## RemoveClaim

`msg_type` = `0x0010`. Removes a claim. Answered with `Done`.

| Field | Encoding |
|---|---|
| `name` | string, 256 bytes: the principal |
| `claim_name` | string, 255 bytes |

Removing a claim the principal does not hold is `Done` and changes
nothing.
