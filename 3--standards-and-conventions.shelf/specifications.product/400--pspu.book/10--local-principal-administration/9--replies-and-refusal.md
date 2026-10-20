---
title: Replies and Refusal
description: Created, Done and Failed; the five reasons a request is refused; and what a change must have done before it is acknowledged.
---

Every request has exactly one successful reply, listed in §10.A, and any
request may instead be answered with `Failed`.

## Created

`msg_type` = `0x8004`. Body: `rid`, a `u32`. Answers `Add` and
`GroupCreate`: the two requests that allocate a RID, and so have
something to report.

## Done

`msg_type` = `0x8005`. Empty body. Answers every other request that
changes the store.

## Failed

`msg_type` = `0x8006`. The request was refused.

| Field | Encoding |
|---|---|
| `failure` | `u32`: why, from the table below |
| `reason` | string, 512 bytes: why, in words |

| Value | Failure | Means |
|---|---|---|
| `1` | `Denied` | The caller may not administer the store (§10.3). |
| `2` | `NotFound` | Nothing in the store by the name, or the key, given. |
| `3` | `Exists` | The name asked for is already held. |
| `4` | `Invalid` | Well-formed, and asking for something the store will not do. |
| `5` | `Internal` | The store could not be read or written. |

The enumeration is closed (§10.4). `failure` is for a client that
branches on it; `reason` is for a person, and a client SHOULD show it as
it is rather than interpret it.

A store daemon MUST answer a request it cannot decode, or whose
`msg_type` this chapter does not define, with `Invalid`.

There is no failure for "you may not see that". Administering is not
authenticating, and a caller already allowed to administer the store
has nothing to learn from a refusal that it could not learn by listing.

## A change is applied whole, or not at all

A store daemon MUST NOT acknowledge a change, with `Created` or `Done`,
before it has been made durable. A change that cannot be saved MUST be
undone and answered `Internal`; a refused request MUST leave the store as
it was.

Every change acknowledged is also announced to the authority, as PSI's
`Changed` (§2.17), so that what it answers next reflects it. A client
here is told nothing when somebody else changes the store: one that shows
the store SHOULD read it again after its own changes and from time to
time.
