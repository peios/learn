---
title: Scope and Roles
description: What PLPS specifies — how a program administers a local principal store through the daemon that owns it — and its two roles.
---

This chapter specifies **PLPS**, the protocol on which a program
administers a **local principal store**: the users and groups a machine
holds for itself, their memberships, their credentials and their claims.
It is spoken to the daemon that owns the store, never to the store's
file.

Two roles participate.

The **store daemon** owns the store. It is the store's only reader and
only writer, it decides who may administer it, and it applies each
request or refuses it. On Peios it is `lpsd`, which is also the machine's
local principal source on PSI (§2): the store it administers here is the
one it answers for there.

The **administrator client** is a program that asks: a command-line tool
such as `lps`, a desktop app such as Principals Manager, or a
provisioning tool. It holds no state of its own and no privilege of its
own; everything it does is a request the store daemon decides whether to
honour. Any program MAY be an administrator client, and a third party
writing one is the case this chapter is written for.

## Why a daemon, and not the file

The store holds every local principal's credential verifier, so its
descriptor admits the store daemon and nothing else. A tool that edited
the file would need that descriptor widened to whatever it runs as,
undoing the one thing it exists to do. Going through the daemon keeps one
writer, makes "an administrator may do this" a check on the caller's
token rather than a file permission, and lets the daemon validate every
change before anything is written.

This chapter covers:

- the channel: where it is, who may connect, and the one exchange each
  connection carries (§10.3)
- message framing, shared with PGSS Logon (§10.4)
- the requests: principals (§10.5), groups and membership (§10.6),
  claims (§10.7), and SSH keys and credential policy (§10.8)
- the replies, and how a request is refused (§10.9)
- the obligations binding on each role (§10.10)

This chapter does not cover:

- How the store is kept on disk, or how a credential verifier is
  derived — the store daemon's own design.
- Signing in, and a principal changing their own password. Those are
  PGSS Logon, and reach the store through PSI (§2.21).
- Looking principals up. Anyone may ask who a name or a SID is, and who
  is in a group, on the authority's identity socket (PGSS §2.14); a
  client that only reads SHOULD read there rather than here, since that
  socket answers everyone.
- What policy applies to a principal at sign-in, such as its privileges.
  That is the authority's (PGSS §2.13).
