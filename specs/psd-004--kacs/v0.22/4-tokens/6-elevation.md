---
title: Linked Tokens and Elevation
---

At logon time, authd MAY create two tokens for the same principal, linked together:

- **Elevated token** (`elevation_type = Full`) — the user's complete identity: all groups active, all assigned privileges present and enabled.
- **Filtered token** (`elevation_type = Limited`) — the same user SID, but administrative groups set to deny-only, dangerous privileges stripped. Created from the elevated token via FilterToken.

Both tokens MUST belong to the same LogonSession. The filtered token is installed as the LogonSession's default. The elevated token exists but is not directly accessible to unprivileged processes.

A token with no linked pair has `elevation_type = Default`.

## KACS responsibilities

KACS provides pairing, storage, and query restriction:

- **Linked pair association** — the pair is registered on the LogonSession. Given either token, the system can retrieve the partner. The pairing is managed at the LogonSession level, not stored on individual token objects.
- **Elevation type classification** — `elevation_type` on each token so consumers can determine which side they hold.
- **Identification-level query restriction** — when an unprivileged caller queries a token's linked token, KACS MUST return a copy at Identification impersonation level. The caller can inspect the elevated token but MUST NOT use it for access control decisions. A caller holding `SeTcbPrivilege` receives a full handle to the actual linked token.

> [!INFORMATIVE]
> Returning a token copy via TOKEN_QUERY is an intentional exception to the normal access-right model, where TOKEN_DUPLICATE would be expected. The exception exists because the returned copy is always Identification-level — functionally a query result, not a usable token.

## KACS non-responsibilities

The actual elevation decision — "should this user be allowed to use their elevated token right now?" — is entirely authd's responsibility. KACS MUST NOT gate elevation, verify credentials, or display prompts. KACS stores the pair and restricts unprivileged access to it.

## Lifecycle

Both tokens in a linked pair share a LogonSession. When a LogonSession is destroyed (last token refcount drops to zero), the pair linkage is removed and the pair's own references to both tokens are dropped. However, token objects are refcounted — if a process still holds a token fd or a credential still references the token, the token object itself survives until all references are released. After the pair is unlinked, querying the linked token (KACS_IOC_GET_LINKED_TOKEN) returns an error — the partner relationship no longer exists, even if the individual token objects are still live.
