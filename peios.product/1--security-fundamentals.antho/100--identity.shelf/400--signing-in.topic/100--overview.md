---
title: Signing in
type: concept
description: How a sign-in works on Peios — the conversation with the authority on /run/logon.sock, the roles involved, and why authentication and derivation are separate.
related:
  - peios/logon-sessions/overview
  - peios/logon-sessions/logon-types
  - peios/managing-local-principals/overview
  - peios/tokens/overview
  - peios/signing-in/the-login-command
---

Every sign-in on Peios is a conversation with an **authority** over a Unix socket at `/run/logon.sock`. The protocol is PGSS Logon, and it is a conformance requirement rather than an implementation detail: a system that does not offer it, at that path, with these semantics, is not Peios.

Knowing its shape is worth the few minutes it takes. It explains why a login prompt behaves the way it does, why a wrong password and an unknown account are indistinguishable, and what you would have to build to add a new way of signing in.

## Three roles

**The authority** listens on the logon socket. It decides whether a sign-in succeeds, and it is the only thing on the system that mints tokens. On a stock Peios system that is `authd`. There is at most one on a running system — two would make "who authenticated this?" unanswerable.

**The client** connects and speaks on the principal's behalf. `login` is a client. So is any greeter, remote access daemon or kiosk agent you might write. A client renders the prompts it is asked to render, returns the answers, and installs the token it is given. It is not trusted, and nothing it sends is taken as fact.

**A principal source** knows who exists and verifies credentials. It asserts an identity and can do nothing else — it cannot mint a token, grant a privilege or create a session, because the protocol it speaks has no message for any of those. `lpsd` is the local one. See [managing local principals](~peios/managing-local-principals/overview).

## The conversation

A client opens a connection and sends one `LogonStart`, naming the principal, the kind of session it wants, and **the credential types it is able to collect**. The authority may then ask for credentials — as many rounds as the source needs — and each request carries prompts the client renders without interpreting. The conversation ends when the authority grants or denies.

The capability list is a statement about the client, not a demand. Declaring that you can collect a password does not mean one will be asked for; declaring that you can collect nothing says you are able to complete a sign-in that needs no interaction, and nothing else. An authority faced with that either completes the sign-in or denies it. That is the mechanism behind [passwordless accounts](~peios/managing-local-principals/creating-accounts) and console autologon.

A connection carries exactly one conversation, so the connection is the conversation's identity. There is no correlation identifier to forge.

## The authority is not a process factory

A grant carries a token as a file descriptor, a session identifier, and a profile. It carries nothing about what should happen next, because nothing about what happens next is the authority's concern.

The client installs the token itself and proceeds. `login` makes the token its own and then `exec`s your shell, rather than the authority forking anything. This keeps the most privileged process on the system out of the business of launching programs: `authd` never learns about terminals, environments or session leadership, and stays small enough to audit.

It also means a client can obtain a token for a purpose the authority never anticipated.

## Authentication and derivation are separate

Two acts, deliberately distinguished.

**Authentication** establishes that the principal is who they claim. Its output is an identity and nothing more.

**Derivation** constructs the token — which SIDs it carries, which privileges, at what integrity level, with what projected identifiers. Its inputs are the authenticated identity **and this machine's policy**.

The separation is what stops an identity established elsewhere from carrying entitlements onto this machine with it. A directory can tell this machine that you are a member of `Domain Admins`; whether that membership carries `SeLoadDriverPrivilege` here is answered here, every time, by the authority applying local policy. An authority never accepts a token, a privilege set or an integrity level from another party, whatever its trust level.

See [privileges](~peios/privileges/overview) for what that policy contains.

## What the authority does not trust

Nothing a client sends. Three consequences are worth knowing because you will see them from the outside:

**Peer identity comes from the socket.** The authority reads the connected peer's token from the kernel rather than believing anything in a message, because there is no field a client could put its identity in that it could not also lie in. `SO_PEERCRED` is not used: it returns the projected uid, and on Peios many principals project to the same number.

**The logon type is a proposal.** Only the caller knows whether a connection is an interactive shell or a batch command, so the caller says — and the authority constrains that against what the verified peer is permitted to request. See [logon types](~peios/logon-sessions/logon-types).

**The identifier is a claim** until authentication succeeds, and `tty` and `remote_host` are never more than that. A client that lies about its remote host is not prevented from doing so by this protocol.

## A wrong password and an unknown account look identical

An authority never distinguishes an unknown principal from a bad credential — not by denial code, not by the text it returns, and not by timing. There is one denial for both.

`lpsd` holds to the timing half by verifying an unknown name against a decoy: a real verifier over a password nobody knows, so both outcomes cost one full derivation. Returning early for a name it did not recognise would make "does this account exist?" answerable by anyone who can time a sign-in.

Account **existence** is not a secret, and Peios does not pretend otherwise — it is answered plainly on a different socket, `/run/ident.sock`, which is how `ls -l` turns an owner into a name. What the logon socket refuses to do is let you learn it by guessing credentials. See [resolving names](~peios/managing-local-principals/resolving-names).

## Where to start

- [The `login` command](~peios/signing-in/the-login-command) — the terminal client, and how a live image signs in without being asked anything.
- [Logon sessions](~peios/logon-sessions/overview) — the kernel object a successful sign-in creates.
- [Managing local principals](~peios/managing-local-principals/overview) — the accounts being signed in to.

The protocol is specified rather than merely documented: [PGSS §2](~peios/logon/scope-and-roles) is Logon, and [PSPU §2](~peios/principal-source-interface/scope-and-roles) is PSI, the interface principal sources speak. Read those if you are writing a client or a source of your own.
