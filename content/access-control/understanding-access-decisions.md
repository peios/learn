---
title: Understanding Why an Access Decision Was Made
type: how-to
order: 170
---

When access is denied unexpectedly — or granted when it shouldn't be — use `sd explain` to see exactly how AccessCheck evaluated the request.

## Explain an access decision

Provide an object, a process (or thread), and the rights to check:

```
$ sd explain /srv/data/reports 1482 FILE_READ_DATA
Token:   S-1-5-19 (Local Service)
Object:  /srv/data/reports
Request: FILE_READ_DATA

[1] Integrity check
    Token integrity:  System
    Object label:     High
    Result:           pass

[2] Owner check
    Owner: S-1-5-21-...-1013 (alice)
    Token user: S-1-5-19 (Local Service)
    Not owner — no implicit rights

[3] DACL walk
    ACE 1: Deny  bob  FILE_WRITE_DATA
           SID match: no — skip
    ACE 2: Allow alice FILE_ALL_ACCESS
           SID match: no — skip
    ACE 3: Allow Domain Users FILE_READ_DATA
           SID match: no — skip
    Requested rights remaining: FILE_READ_DATA

[4] Privilege overrides
    No applicable privileges

Result: DENIED — FILE_READ_DATA not granted by any ACE
```

The output walks through each stage of the AccessCheck pipeline, showing exactly which checks passed, which ACEs were considered, and where the decision was made.

## Diagnosing common patterns

**Denied by integrity:**

```
[1] Integrity check
    Token integrity:  Medium
    Object label:     High
    Result:           DENIED — token integrity below object label
```

The process's integrity level is too low. The DACL is never reached.

**Denied by a deny ACE:**

```
[3] DACL walk
    ACE 1: Deny  bob  FILE_WRITE_DATA
           SID match: yes (token user)
           FILE_WRITE_DATA — DENIED
```

A deny ACE matched before any allow could grant the right.

**Denied because no ACE matched:**

```
[3] DACL walk
    ACE 1: Allow alice FILE_ALL_ACCESS
           SID match: no — skip
    ACE 2: Allow Domain Users FILE_READ_DATA
           SID match: no — skip
    Requested rights remaining: FILE_READ_DATA

Result: DENIED — FILE_READ_DATA not granted by any ACE
```

The token's SIDs don't match any allow ACE. The process is not in any group that has access.

**Granted by privilege override:**

```
[3] DACL walk
    Requested rights remaining: WRITE_OWNER

[4] Privilege overrides
    SeTakeOwnershipPrivilege: enabled
    WRITE_OWNER — granted via privilege

Result: GRANTED
```

The DACL didn't grant the right, but a privilege did.

## Explain with a specific thread

Use `pid/tid` to check a thread's impersonation token instead of the primary:

```
$ sd explain /srv/data/reports 1482/1509 FILE_READ_DATA
Token:   S-1-5-21-...-1013 (alice)  [impersonation]
...
```

## Structured output

For scripting and automation:

```
$ sd explain --json /srv/data/reports 1482 FILE_READ_DATA
```

Returns the full evaluation trace as structured data — each stage, each ACE considered, and the final result.
