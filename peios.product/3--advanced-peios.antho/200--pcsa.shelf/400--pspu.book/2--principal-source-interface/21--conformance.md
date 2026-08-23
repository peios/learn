---
title: Conformance
description: Every requirement of this chapter collected by role, for an authority federating over PSI and for a source serving it.
---

A conforming implementation MUST satisfy every requirement in this
chapter. This section collects them by role.

## Authority obligations

An authority federating over PSI MUST satisfy all of the following.

### Channel

1. Listen; never dial out to a source (§2.3).
2. Never rely on the socket's descriptor as the access control, and
   bound unregistered connections and registration time independently of
   it (§2.6).
3. Bound registered sources, and conversations per source (§2.6).
4. Tear down the connection on a framing error or a failed write, rather
   than attempting resynchronisation (§2.6).

### Registration

5. Require `Register` on conversation `0` as the first message (§2.8).
6. Establish the source's identity from the peer's token, never from
   `source_name`, and refuse a mismatch rather than correcting it
   (§2.8, §2.9).
7. Accept only configured sources, treating an empty configuration as
   *no source may register* (§2.9).
8. Refuse a source that declares no domain (§2.10).
9. Refuse a domain that is not a well-formed locally-issued domain SID
   (§2.10).
10. Refuse a domain another registered source claims (§2.10).
11. Refuse a source declaring a different domain from the one it
    declared before (§2.10).
12. Refuse a source whose declared domain contradicts a configured pin,
    and treat an unparseable pin as refusing rather than as absent
    (§2.10).
13. Send `Registered` only once the source is routable (§2.8).
14. Report, where an administrator will see it, a source registering
    with no identifier range, and a source registering without
    `QUERIES` (§2.8).

### Conversations

15. Allocate conversation identifiers, never accepting one from a
    source, never opening one with an identifier already live, and
    reserve `0` for registration (§2.7).
16. Route each logon to exactly one source, resolved before any
    credential is collected (§2.11).
17. Never fall back to another source when the owning source is
    unreachable (§2.11).
18. Relay the verified `originator`, taken from the client's socket
    (§2.11).
19. Refuse to relay a prompt for a credential type the client did not
    advertise (§2.12).
20. Enforce its own round and time limits on the relayed exchange
    (§2.12).
21. Send `Abandon` for any conversation that will not reach a terminal
    state (§2.14).

### Assertions

22. Validate every SID structurally before treating it as identity,
    including SIDs carried inside claim values (§2.13).
23. Drop an asserted logon SID, and drop duplicates first-mention-wins,
    **before** applying any scope test (§2.13).
24. Enforce identity confinement, with no configuration lifting it, on
    an `Assertion`, on a `QueryResult`, and on the `sid` of a `Changed`
    (§2.18).
25. Enforce membership scope, subject only to a per-source permission
    covering memberships alone, and apply it to a **source-asserted**
    `primary_group` as well as to listed groups — promoting an unlisted
    one into the membership set before the test (§2.19, §2.13).
26. Never apply membership scope to a `primary_group` it substituted
    itself for an empty field (§2.13, §2.19).
27. Fail the logon on a malformed group SID, an unusable claim, a
    `canonical_name` PGSS §2.15 forbids, or an out-of-range identifier
    (§2.13).
28. Place `primary_group` on the token even when the source did not list
    it among `groups` (§2.13).
29. Perform derivation itself, and never accept privileges, integrity,
    or a token from a source (§2.4).
30. Never relay a refusal reason revealing a distinction the source was
    required not to make (§2.13).

### Identifiers

31. Apply the source's base to every relative identifier it accepts, and
    never accept one already rebased (§2.20).
32. Refuse a relative identifier of `0` or one at or past the source's
    count, rather than clamping or wrapping it (§2.20).
33. Reserve a band of identifiers below every source's base for its own,
    and use its own value for any SID within that band regardless of
    what the source sent (§2.20).

### Queries

34. Never send a message a source did not declare it answers, and never
    set a field bit gating a capability it did not declare (§2.8).
35. Never send more keys in one `Query` than the source's `max_batch`,
    nor more than 64 whatever it declared (§2.8).
36. Resolve an absolute POSIX identifier to a source and a relative
    identifier itself, and never send an absolute one to a source
    (§2.15).
37. Apply identity confinement, membership scope and numeric scope to a
    `QueryResult` exactly as to an `Assertion`, and validate every SID
    in one structurally — including those of references inside a value
    (§2.15).
38. Rebase every identifier in a result, under the rules of §2.20
    (§2.15).
39. Qualify a source's `canonical_name` itself; never require a source
    to (§2.15).
40. Consult no further source on a `Refused` result, treat only
    `NotFound` as leave to continue, and never relay a source's
    `Refused` outward as PGSS Logon's `Refused` outcome (§2.15).
41. Never record a source it may not ask — one that declared no
    `QUERIES` — as having answered `NotFound` (§2.15).
42. Relay cursors opaquely, never construct or modify a source's, and
    never restart an enumeration on a source's behalf (§2.16).
43. Record a source that declined or could not be reached, and not retry
    it for the remainder of that enumeration, across pages as well as
    within one (§2.16).
44. Never infer from a source declining to enumerate that it holds
    nothing (§2.16).

### Caching

45. Not cache a source's answers at all unless it declared
    `PUSHES_CHANGES` or a non-zero `entry_ttl` (§2.8, §2.17).
46. Not hold an answer beyond a declared `entry_ttl` (§2.8).
47. Accept `Changed` at any time after `Registered`, and never reply to
    it (§2.17).
48. Re-read through `Query` after an invalidation, and never take a new
    value from `Changed` (§2.17).
49. Treat the loss of a source's connection as `All` for that source
    (§2.17).

An authority that holds nothing satisfies 45 to 49 trivially.

## Source obligations

A principal source MUST satisfy all of the following.

### Connection

1. Connect to the authority; never listen for it (§2.3).
2. Open with `Register` on conversation `0`, carrying its name and its
   domain (§2.8).
3. Send nothing else before receiving `Registered` (§2.8).
4. Report itself ready — to an init system or equivalent — only after
   `Registered` (§2.3).
5. Declare the same domain on every registration, for the life of the
   machine's configuration (§2.10).
6. Tear down the connection on a framing error or a failed write, on
   every path including an unsolicited `Changed` (§2.6, §2.17).

### Conversations

7. Reply on the conversation identifier it was given, and never invent
   one (§2.7).
8. Decline to act on a message on a conversation it does not know, and
   never treat it as opening one — without replying on it, since the
   identifier may since have been reused (§2.7).
9. Refuse an `Authenticate`, `Query` or `EnumerateSource` arriving on
   conversation `0` (§2.7).
10. Bound the conversations it tracks itself, rather than relying on the
    authority's limit (§2.6).
11. Refuse beyond that bound with `AuthorityUnavailable`, rather than
    dropping silently (§2.11).
12. Discard conversation state on `Abandon`, and not reply (§2.14).

### Answering

13. Send exactly one terminal message — `Assertion` or `Refusal` — per
    conversation (§2.13).
14. Assert only principals within its declared domain (§2.18).
15. Assert group SIDs and identifiers only, never attributes (§2.13).
16. Carry the canonical spelling of the principal's name in
    `canonical_name` (§2.13), and never assert a name that PGSS §2.15
    forbids — validating what it asserts, not only what it creates.
17. Never distinguish an unknown principal from a bad credential — by
    denial code, by reason, or by timing (§2.13).

### Identifiers

18. Assert **relative** identifiers only, and never apply its own base
    (§2.20).
19. Allocate from a single counter across every kind of object it holds,
    so that no number is issued twice (§2.20).
20. Send `0` for any object it does not number, including every group it
    does not own (§2.20).
21. Never issue an identifier at or past the count it was given (§2.20).

### Queries

A source declaring no capabilities (§2.8) is exempt from this section
entirely.

22. Declare only capabilities it implements, and answer every message
    type it declared (§2.8).
23. Answer every key of a `Query`, in order, without reordering, merging
    or omitting — or refuse the conversation whole (§2.15).
24. Send `Found`, `NotFound` or `Refused` in a result, and never
    `Unavailable` or `Malformed` (§2.15).
25. Return its own canonical spelling of a name, unqualified (§2.15).
26. Return **relative** identifiers in a result, exactly as in an
    `Assertion` (§2.15, §2.20).
27. Answer only for principals within its declared domain, on a query as
    on a logon (§2.18).
28. Answer `Refused`, never an empty `Found`, wherever it is declining
    rather than reporting an absence — including a membership it will
    not expose, a key naming an object it does not hold, and a key of
    the wrong kind (§2.16).
29. Refuse a cursor it can no longer honour, rather than restarting or
    answering from a changed store (§2.16).
30. Hold no per-cursor state it is unwilling to discard unasked (§2.16).
31. Size a page against the smaller of PSI's message ceiling and PGSS
    Logon's, since the authority must re-encode it into the latter
    (§2.16, §2.A).
32. Send `Changed` before the altered answer becomes observable, if it
    declared `PUSHES_CHANGES` (§2.17).
33. Declare a non-zero `entry_ttl` if it does not push changes and can
    tolerate its answers being held, and SHOULD declare one even if it
    does (§2.8, §2.17).

### Credentials

34. Store verifiers that are **not** usable as credential material —
    nothing a challenge could be recomputed from (PGSS §2.11).
35. Erase credential material, and every buffer it was decoded through,
    before that memory is released (PGSS §2.12).
36. Never write credential material to a log, audit record, or
    diagnostic (PGSS §2.12).

## What a source is not required to do

A source is **not** required to store anything, to be local, to be
persistent, or to know what a token is. It answers one question: given
this identifier and whatever it chose to ask for, who is this?

Nor is it required to trust the authority beyond the connection. A
source that refuses logons on the strength of `originator`, or declines
to answer for principals it holds but does not wish to expose, is
conforming.
