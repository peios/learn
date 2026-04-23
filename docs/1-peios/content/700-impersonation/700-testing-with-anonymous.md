---
title: Testing Public Accessibility with Anonymous Impersonation
type: how-to
description: Using Anonymous impersonation to test whether a resource is publicly accessible without revealing caller identity.
---

Anonymous impersonation lets you test whether a resource is accessible without any specific identity — answering the question "can everyone access this?"

## Why use Anonymous impersonation

A service might need to determine whether a resource is publicly accessible before deciding how to handle a request. Rather than checking the security descriptor manually and interpreting the ACEs, the service can impersonate at Anonymous level and attempt the access. If it succeeds, the resource is public. If it fails, the resource requires a specific identity.

This is simpler and more reliable than parsing ACEs — it uses the same AccessCheck path that a real anonymous caller would take, including integrity checks, privilege evaluation, and all other pipeline stages.

## How it works

A service thread impersonates the connection at Anonymous level. The impersonation token carries the Anonymous SID (`S-1-1-7`) — a generic identity with no group memberships and no privileges.

```
impersonate_anonymous()

// Attempt the access — evaluated as Anonymous
result = try_open(resource_path, FILE_READ_DATA)

revert_to_self()

if result.succeeded:
    // Resource is publicly readable
else:
    // Resource requires authentication
```

## From the command line

You can test public accessibility using `sd explain` with the Anonymous SID:

```bash
$ sd explain /srv/public/readme.txt --as-anonymous FILE_READ_DATA
Token:   S-1-1-7 (Anonymous)
Object:  /srv/public/readme.txt
Request: FILE_READ_DATA

[3] DACL walk
    ACE 1: Allow  S-1-1-0 (Everyone)  FILE_READ_DATA
           SID match: yes
           FILE_READ_DATA — granted

Result: GRANTED
```

The Everyone SID (`S-1-1-0`) matches the Anonymous identity, so the file is publicly readable.

```bash
$ sd explain /srv/data/reports/q4.pdf --as-anonymous FILE_READ_DATA
Token:   S-1-1-7 (Anonymous)
Object:  /srv/data/reports/q4.pdf
Request: FILE_READ_DATA

[3] DACL walk
    ACE 1: Allow  S-1-5-11 (Authenticated Users)  FILE_READ_DATA
           SID match: no — skip
    Requested rights remaining: FILE_READ_DATA

Result: DENIED — FILE_READ_DATA not granted by any ACE
```

The ACE grants access to Authenticated Users, which does not include Anonymous. The file requires authentication.
