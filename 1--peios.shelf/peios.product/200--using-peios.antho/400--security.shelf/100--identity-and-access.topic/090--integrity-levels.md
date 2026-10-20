---
title: Integrity Levels
type: concept
description: How integrity levels rank the trust of programs and objects, the five standard levels, and how the integrity check stops a less trusted program from changing a more trusted object.
related:
  - peios/identity-and-access/access-tokens
  - peios/permissions/object-policy
  - peios/application-boundaries/process-trust
---

An integrity level ranks how far Peios trusts a program or an object. Every
access token has one, and objects can carry one. Before Peios reads an
object's permissions, it compares the two levels. A program at a lower level
can't change an object at a higher level, even if the object's permissions
would otherwise allow it. A program handling untrusted input can therefore
run at a low level, so that a fault in it can't change the system's own files
and settings.

## The levels

Five levels are standard:

| Level | Value | Used for |
|---|---|---|
| Untrusted | 0 | Code in a sandbox |
| Low | 4096 | Services handling untrusted input |
| Medium | 8192 | Ordinary sign-ins and most services |
| High | 12288 | Administrators |
| System | 16384 | The kernel, peinit, and the system's most trusted services |

A level is written as a security identifier (SID) in the form `S-1-16-n`,
where *n* is the value. Peios compares the numbers, so a value between two
standard levels is valid too.

Your sign-in gets its level from machine policy. A token is Medium by default,
and the policy that Peios ships gives Administrators High. A token's level
can't be changed after it is created. A program file can be marked to run at
a lower level than its parent, but nothing raises a running program's level.

## The integrity check

Each object can carry a label with its level. An object without a label is
treated as Medium.

By default, a program can read an object at a higher level but can't write to
it. A label can also stop a lower-level program from reading the object or
running it. The integrity check comes before the object's permissions, and it
can only take access away: a permission can't grant what the integrity check
refuses. Rights that come from a privilege aren't removed by it.

## Integrity and process trust

Integrity levels are a property of the token, so they follow the identity a
program acts with. Process Integrity Protection is a separate mechanism that
follows the program itself, based on the signature of its program file. See
[Process Trust](~peios/application-boundaries/process-trust).

The kernel documents [mandatory integrity control](~kernel/internals/kacs/access-check/mandatory-integrity-control)
in full.
