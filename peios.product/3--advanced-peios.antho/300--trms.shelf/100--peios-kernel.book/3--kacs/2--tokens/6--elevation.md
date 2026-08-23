---
title: Linked Tokens and Elevation
description: Two linked tokens for one principal — what the kernel does with the link, what it deliberately leaves to userspace, and the pair's lifecycle.
---

At logon, authd may create two tokens for one principal and link them.
The **elevated token**, `elevation_type = Full`, carries the user's
complete identity: every group active, every assigned privilege
present and enabled. The **filtered token**,
`elevation_type = Limited`, carries the same user SID with
administrative groups set to deny-only and dangerous privileges
stripped, produced from the elevated token by FilterToken.

Both tokens belong to the same LogonSession, are both primary tokens,
and carry the same user SID. The filtered token is installed as the
LogonSession's default; the elevated token exists but is not directly
reachable by unprivileged processes.

A token never assigned a linked-pair role has
`elevation_type = Default`. Once `KACS_IOC_LINK_TOKENS` sets a token
object to Full or Limited, that role is sticky on that object. If the
pair is later replaced or destroyed the token has no active partner
and `KACS_IOC_GET_LINKED_TOKEN` returns an error, but the token goes
on reporting its last assigned elevation type.

## What KACS does

KACS provides pairing, storage, and query restriction — three
mechanisms, no policy.

**Linked pair association** registers the pair on the LogonSession, so
given either token the system can retrieve its partner. The pairing
lives at the LogonSession level and is not stored on the token
objects.

Establishing a pair is a TCB operation: the caller holds
`SeTcbPrivilege` on its **primary** token — an impersonating thread's
effective token does not satisfy it — and holds `TOKEN_DUPLICATE` on
*both* of the token handles being linked. The two handles have to name
distinct token objects, and both have to belong to the LogonSession
named in the request, which itself has to be published. The ioctl
ignores the handle it was issued on entirely; only the two named
handles matter.

**Elevation type classification** puts `elevation_type` on each token
so a consumer can tell which side it is holding.

**Identification-level query restriction** governs what an unprivileged
caller gets when it queries a token's partner: a deep clone at
Identification impersonation level. The clone follows DuplicateToken
semantics — a new token object, a new `token_id`, `modified_id`
initialised to it, a fresh default descriptor — except that it
preserves the partner's `elevation_type`, and it is always returned
through a `TOKEN_QUERY`-only handle. The caller can inspect the
elevated token but cannot use it for an access decision. A caller
holding `SeTcbPrivilege` receives a full handle to the actual linked
token instead.

Returning a copy through `TOKEN_QUERY` is a deliberate exception to
the normal access-right model, where `TOKEN_DUPLICATE` would be
expected. It holds because the returned copy is always
Identification-level: functionally a query result rather than a usable
token.

## What KACS does not do

The elevation decision itself — whether this user should be allowed to
use their elevated token right now — is entirely authd's. KACS does
not gate elevation, verify credentials, or display prompts. It stores
the pair and restricts unprivileged access to it.

Beyond enforcing the LogonSession, token-type and same-user
invariants, KACS does not verify that the filtered token really is a
FilterToken-derived reduction of the elevated one. That correspondence
is authd's to get right.

## Lifecycle

Both tokens in a pair share a LogonSession, and that session is not
destroyed while any token fd, credential, pair slot, or other
reference keeps one of its token objects live. When the last external
reference is released and only the linked-pair's own references
remain, KACS destroys the LogonSession, removes the linkage, and drops
the pair's references to both tokens. After that cleanup no token
object from the session remains live purely because it was linked.

Stale-role tokens can exist before final destruction — for instance
when `KACS_IOC_LINK_TOKENS` replaces a LogonSession's active pair
while an old token object is still held by an fd or credential. Fork
produces them too: the deep copy a child receives preserves the
parent's elevation type, so a forked child can hold a Full or Limited
token that was never linked to anything. Once a
token is no longer the active member of the pair, querying its linked
token returns an error, because the partner relationship no longer
exists for it. Such survivors keep their sticky Full or Limited
elevation type: they are stale-role tokens with no active partner, not
Default tokens.
