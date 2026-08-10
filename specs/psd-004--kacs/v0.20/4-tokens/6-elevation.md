---
title: Linked Tokens and Elevation
---

At logon time, authd MAY create two tokens for the same principal, linked together:

- **Elevated token** (`elevation_type = Full`) — the user's complete identity: all groups active, all assigned privileges present and enabled.
- **Filtered token** (`elevation_type = Limited`) — the same user SID, but administrative groups set to deny-only, dangerous privileges stripped. Created from the elevated token via FilterToken.

Both tokens MUST belong to the same LogonSession, MUST be primary tokens, and MUST carry the same user SID. The filtered token is installed as the LogonSession's default. The elevated token exists but is not directly accessible to unprivileged processes.

A token that has never been assigned a linked-pair role has
`elevation_type = Default`. Once KACS_IOC_LINK_TOKENS sets a token object's
`elevation_type` to Full or Limited, that role is sticky on that token object.
If the pair is later replaced or destroyed, the token no longer has an active
partner and KACS_IOC_GET_LINKED_TOKEN returns an error, but the token continues
to report its last assigned Full or Limited elevation type.

## KACS responsibilities

KACS provides pairing, storage, and query restriction:

- **Linked pair association** — the pair is registered on the LogonSession. Given either token, the system can retrieve the partner. The pairing is managed at the LogonSession level, not stored on individual token objects.
- **Elevation type classification** — `elevation_type` on each token so consumers can determine which side they hold.
- **Identification-level query restriction** — when an unprivileged caller queries a token's linked token, KACS MUST return a deep clone at Identification impersonation level. The clone follows DuplicateToken semantics for independent object creation (new token object, new `token_id`, `modified_id` initialized to the new `token_id`, fresh default token SD), except that it preserves the partner token's `elevation_type` and is always returned through a `TOKEN_QUERY`-only handle. The caller can inspect the elevated token but MUST NOT use it for access control decisions. A caller holding `SeTcbPrivilege` receives a full handle to the actual linked token.

> [!INFORMATIVE]
> Returning a token copy via TOKEN_QUERY is an intentional exception to the normal access-right model, where TOKEN_DUPLICATE would be expected. The exception exists because the returned copy is always Identification-level — functionally a query result, not a usable token.

## KACS non-responsibilities

The actual elevation decision — "should this user be allowed to use their elevated token right now?" — is entirely authd's responsibility. KACS MUST NOT gate elevation, verify credentials, or display prompts. KACS stores the pair and restricts unprivileged access to it. Beyond enforcing the LogonSession, token-type, and same-user invariants, KACS is not responsible for proving that the filtered token is an exact FilterToken-derived reduction of the elevated token.

## Lifecycle

Both tokens in a linked pair share a LogonSession. A LogonSession is not destroyed while any token fd, credential, pair slot, or other token reference keeps a token object in that LogonSession live. When the last external token reference has been released and only the linked-pair-owned references remain, KACS destroys the LogonSession, removes the pair linkage, and drops the pair's own references to both tokens. After this final LogonSession-destruction cleanup, no token object from that LogonSession is expected to remain live solely because it was linked.

Stale-role live tokens can exist before final LogonSession destruction, for example when KACS_IOC_LINK_TOKENS replaces a LogonSession's active linked pair while an old token object is still referenced by an fd or credential. After a token is no longer the active member of the LogonSession pair, querying the linked token (KACS_IOC_GET_LINKED_TOKEN) returns an error — the partner relationship no longer exists for that token. Such surviving token objects retain their sticky Full or Limited `elevation_type`; they are stale-role tokens with no active partner, not Default tokens.
