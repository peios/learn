---
title: Conformance
description: Every requirement of this chapter collected by role — the store daemon and the administrator client.
---

## A conforming store daemon

**The channel.** Decides from the caller's token, before reading the
request, whether the caller may administer the store, admitting `SYSTEM`
and a token carrying `BUILTIN\Administrators` enabled, and treating a
deny-only group as no membership; refuses anyone else with `Denied`
(§10.3). Serves one request a connection, answers it exactly once, and
closes (§10.3).

**Framing.** Checks the magic and the version of every message, refuses
one over 2 MiB unread, and substitutes the stated default for an
appended field a peer did not send (§10.4).

**Requests.** Answers each with its own reply (§10.A) or `Failed`, and a
request it cannot decode or does not define with `Invalid` (§10.9).
Resolves a group as written itself (§10.2). Answers `NotFound` for a
principal, group or key it does not hold, `Exists` for a name already
held, and `Invalid`, with the reason, for anything it will not do
(§10.5 to §10.9).

**Its rules.** Refuses to leave the store with no enabled administrator
who can sign in (§10.5); to delete a group anyone is in or has as their
primary group (§10.6); a claim PSI could not carry (§10.7); and a key it
cannot read, or holds already (§10.8). Gives a principal made without a
password the policy `NoCredential`, and one made with one `Password`
(§10.5). Makes a principal whole or not at all, refusing an `Add` if it
refuses any field of it (§10.5). Keeps a renamed principal's SID, RID,
Unix ID and home directory (§10.5), and a renamed group's SID, RID, Unix
ID and memberships (§10.6). Holds one name for one principal or
local group, matched without regard to case (§10.5, §10.6). Never
reissues a RID (§10.2).

**Changes.** Acknowledges a change only once it is durable, undoes one
it cannot save, leaves the store untouched on a refusal, and announces
every change to the authority (§10.9).

## A conforming administrator client

**The channel.** Opens a connection for each request and holds none
open (§10.3). Treats a connection refused for permission as `Denied`,
and a connection closed without a reply as an outcome unknown, reading
the store again before saying the change failed (§10.3).

**Requests.** Passes a group as the person wrote it, resolving nothing
itself (§10.2). Sends `credential_kind` `0` only where a principal is
meant to need no credential (§10.5). Sends `CredentialPolicy` alongside
`SetPassword` where the password is meant to be used (§10.5). Reads a
principal back with `Show` where it must know that an `Add`'s profile
was applied (§10.5). Shows no credential policy where the store daemon
gave none (§10.5).

**Refusals.** Shows a refusal's `reason` as it is (§10.9).

**Reading.** Reads principals for display on the identity socket where
it need not administer them (§10.1), and reads the store again after its
own changes, since nothing tells it of anyone else's (§10.9).
