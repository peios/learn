---
title: Conformance
description: Every requirement of this chapter collected by role, for an implementation claiming to be a PGSS Logon authority or client.
---

A conforming implementation MUST satisfy every requirement in this
chapter. This section collects them by role.

## Authority obligations

An implementation claiming to be a PGSS Logon authority MUST satisfy all
of the following.

### Channel

1. Listen on `/run/logon.sock` as a `SOCK_STREAM` Unix domain socket
   (§2.5).
2. Control access to it with a security descriptor, not with process
   integrity and not with POSIX permission bits (§2.4).
3. Serve conversations concurrently, so that one stalled logon does not
   block others (§2.5).
4. Support `SCM_RIGHTS` on the channel (§2.9).

### Framing

5. Reject any message whose magic is not `PGSL`, as a whole-connection
   failure (§2.6).
6. Reject any message whose version it does not implement, answering
   `UnsupportedVersion` where it can still encode a denial (§2.6).
7. Reject any message declaring more than 65536 bytes, or fewer than a
   header, without reading the body (§2.6).
8. Skip to a structure's declared end after reading known fields, rather
   than assuming its length, and substitute a documented default for an
   optional trailing field a peer did not write (§2.6).

### Conversation

9. Require `LogonStart` as the first message, and reject a conversation
   opening otherwise (§2.3).
10. Send exactly one terminal message, nothing after it, and close the
    connection (§2.3).
11. Bound the number of rounds, the time spent awaiting an answer, and
    the time a conversation may remain open, and terminate with
    `ConversationLimit` on exhausting any of them (§2.3, §2.5). A bound
    reached MUST produce a terminal message; closing the connection
    silently is what the code exists to prevent.
12. Reject a `CredentialResponse` it did not solicit (§2.3).
13. Match answers to prompts by `credential_ref`, never by position, and
    treat a missing answer as a failed logon rather than as grounds to
    tear down the connection (§2.8).

### Trust

14. Establish peer identity from the connected socket's peer token,
    never from a message body, and never via `SO_PEERCRED` (§2.4).
15. Treat `logon_type` as a proposal and constrain it against the
    verified peer (§2.4).
16. Treat `identifier`, `tty` and `remote_host` as unverified claims
    (§2.4).

### Derivation

17. Perform derivation itself, and never accept a token, privilege set
    or integrity level from another party (§2.1).
18. Never fork or exec on the client's behalf; never learn about
    terminals, environments or session leadership (§2.1).

### Prompting

19. Never send a prompt for a credential type absent from the client's
    `supported_credential_types`, and deny the logon instead if it
    cannot proceed within them (§2.8).
20. Ensure `credential_ref` is unique among the prompts of one request
    (§2.8).

### Result

21. Transfer the token as a file descriptor in the ancillary data of
    `AccessGranted`, never by name (§2.9).
22. Never distinguish an unknown principal from a bad credential — by
    denial code, by reason text, or by timing (§2.10, §2.12).
23. Send `home` and `shell` as absolute paths, or empty, whatever their
    provenance; an authority with no value for a profile field MUST
    leave it empty rather than invent one (§2.9).

### Credential handling

24. Erase credential material, and every buffer it was encoded and
    decoded through — including an allocation abandoned by a buffer that
    grew — before that memory is released (§2.12).
25. Never write credential material to a log, audit record, error
    message or diagnostic (§2.12).

### Identity lookup

26. Listen on `/run/ident.sock` as well as `/run/logon.sock`, as a
    `SOCK_STREAM` Unix domain socket (§2.14).
27. Grant connect access to that socket, by security descriptor, to
    every principal that runs ordinary programs (§2.14).
28. Refuse a message of one socket's range received on the other
    (§2.14).
29. Echo each request's `tag`, and never interpret it otherwise
    (§2.14).
30. Serve requests concurrently, and never let a slow answer on one
    connection delay another (§2.14).
31. Bound the time spent answering a request, and answer `Unavailable`
    rather than waiting indefinitely (§2.14).
32. Ignore ancillary data received on the identity socket (§2.14).

### Resolution

33. Interpret names itself, and never require a client to parse, qualify
    or case-fold one (§2.15).
34. Compare names ASCII case-insensitively, establishing the comparison
    itself rather than delegating it to a source (§2.15).
35. Refuse a name containing a reserved character, a byte outside
    `0x20`–`0x7e`, or a leading or trailing space — whether created
    locally, received in a request, asserted by a source, or carried
    alongside a SID in a reference (§2.15).
36. Resolve bare names in a configured order, never in registration
    order, stopping at the first source that answers (§2.15).
37. Carry the resolved SID and the canonical qualified name on every
    successful reply, whatever form the request used (§2.15).

### Answers

38. Never answer a `Principal` request with a group, or a `Group`
    request with a principal, and establish the kind itself rather than
    relaying a source's (§2.16).
39. Ignore a field bit it does not implement, and never report it as
    present (§2.16).
40. Report each requested field it implements as present or as withheld
    with a reason, never as neither (§2.16).
41. Withhold `MEMBERS` with a reason rather than returning a partial or
    empty list, where it will not or cannot produce it (§2.16).
42. Report `Absent` rather than `Declined` for a group whose membership
    is a rule rather than a record (§2.16).
43. Encode "no POSIX identifier" as zero, and never substitute a number
    a caller could mistake for a real one (§2.16).
44. Answer a `passwd` record, a `group` record, a principal's
    memberships, or a name for a SID, each in one request (§2.16).
45. Never report `NotFound` unless every source in the search order that
    could have answered was consulted and answered (§2.18).
46. Report `Unavailable` where a source earlier in the search order
    could not be reached (§2.18).
47. Never report `NotFound` in place of `Refused` or of a `Restricted`
    field, and never report `Refused` for anything other than a caller
    that may not make the request (§2.18).
48. List every source that did not contribute to an enumeration, and
    never report `Found` on a page it could not produce (§2.17, §2.18).
49. Reject a cursor it did not issue, or can no longer honour, with
    `Malformed` — never by restarting the walk and never by reporting it
    complete (§2.17).
50. Serve member enumeration where it withholds `MEMBERS` as `TooLarge`
    (§2.17).

## Client obligations

There are two client roles, and they are independent. A program may be
either, both, or neither: a logon originator never looks a principal up;
a name resolver does the reverse.

An implementation originating logons MUST satisfy obligations 1 to 20.
An implementation performing identity lookup MUST satisfy 21 to 27.

### Conversation

1. Send exactly one `LogonStart`, as the first message (§2.3).
2. Answer each `CredentialRequest` with exactly one `CredentialResponse`
   (§2.3).
3. Never send a `CredentialResponse` that was not solicited (§2.3).
4. Treat a connection that closes without a terminal message as a failed
   logon, and not retry automatically (§2.3).

### Framing

5. Reject any message whose magic is not `PGSL` (§2.6).
6. Reject any message whose version it does not implement (§2.6).
7. Skip to a structure's declared end after reading known fields (§2.6).

### Capabilities

8. Never declare in `supported_credential_types` a credential type it
   cannot render (§2.7). Declaring fewer than it can render is
   permitted, and an empty list is how a client asks for a logon
   requiring no interaction.
9. Fail the conversation, rather than guess, if it receives a prompt it
   cannot render (§2.8).

### Rendering

10. Display received messages, in order, before the prompts of the same
    request (§2.8).
11. Not interpret or branch on message text, `credential_name`, or
    `reason` (§2.8, §2.10).
12. Echo `credential_ref` back unchanged (§2.8).

### Result

13. Read the token descriptor from the ancillary data of
    `AccessGranted`, and treat an `AccessGranted` without one as a
    failed logon (§2.9).
14. Close the descriptor if it does not install the token (§2.9).
15. Have a fallback for every `profile` field, and treat an empty field,
    and an absent `profile`, identically and not as an error (§2.9).
16. Never execute a relative `shell`, nor resolve a relative `home`
    against its own working directory (§2.9). A `shell` containing no
    separator is relative, and MUST NOT be resolved against a search
    path.
17. Never treat `profile` as a directory lookup, nor cache it as an
    answer about any principal other than the one who just authenticated
    (§2.9).

### Credential handling

18. Collect a credential only where it can establish that its collection
    method meets the type's requirements, and never collect a `Password`
    with echo enabled (§2.12).
19. Never silently truncate an answer to fit its own buffer (§2.12).
20. Erase credential material, and every buffer it was collected and
    encoded through, before that memory is released, and never write it
    to a log, error message or diagnostic (§2.12).

### Identity lookup

21. Forward a name unchanged, and never parse, split, qualify or
    case-fold one (§2.15).
22. Never reuse a `tag` while a request bearing it is outstanding, and
    never assume replies arrive in request order (§2.14).
23. Treat a cursor as opaque: never construct, parse or modify one, nor
    present one to a different authority or across a reconnection
    (§2.17).
24. Continue an enumeration until `next` is empty, never infer
    completion from an empty page, and never present a walk it abandoned
    for any other reason as a complete one (§2.17).
25. Surface an enumeration's `incomplete` list rather than discarding it
    (§2.17).
26. Distinguish `NotFound` from `Unavailable`, and never cache the
    second as though it were the first (§2.18).
27. Never use enumeration to test whether a principal exists (§2.17).

Obligations 24 and 26 bind a client that caches for the lifetime of a
single process just as they bind an authority. A resolver that remembers
"no such user" through an outage will keep reporting it after the outage
ends, and one that reports a failed walk as an empty system does the
same thing to every principal at once.

## What a client is not required to do

A client is **not** required to understand what any credential type
means, what any message says, or why a logon was denied. It renders what
it is given and returns what it collects.

That is the property the whole conversational shape exists to produce,
and a client that starts reasoning about the content of prompts has
given it up — it will need changing the next time an authority's policy
does.
