---
title: Working with Process Security
type: how-to
description: Viewing and tightening process security descriptors and diagnosing process access denials with sd explain.
---

Process security descriptors are inspected and modified with the same `sd` tool used for files.

> [!NOTE]
> **Prerequisites:** WRITE_DAC on the target process to modify its SD. READ_CONTROL to view it.

## View a process's security descriptor

```bash
$ sd show --process 1482
Owner:  S-1-5-19 (Local Service)
Group:  S-1-5-19 (Local Service)

DACL:
  Allow  S-1-5-19          (Local Service)     PROCESS_ALL_ACCESS
  Allow  S-1-5-32-544      (Administrators)    PROCESS_ALL_ACCESS
  Allow  S-1-5-18          (SYSTEM)            PROCESS_ALL_ACCESS
```

## View who can send signals to a process

Look for `PROCESS_TERMINATE` and `PROCESS_SIGNAL` in the DACL:

```bash
$ sd explain --process 1482 3841 PROCESS_TERMINATE
Token:   S-1-5-21-...-500 (Administrator)
Object:  process 1482

[3] DACL walk
    ACE 2: Allow  Administrators  PROCESS_ALL_ACCESS
           SID match: yes
           PROCESS_TERMINATE — granted

Result: GRANTED
```

## Tighten a service's process SD after initialization

A service can reduce its own process DACL once it no longer needs broad management access:

```bash
$ sd set --process $$ \
    allow S-1-5-80-2739571183 PROCESS_ALL_ACCESS \
    allow S-1-5-18 PROCESS_ALL_ACCESS
```

This removes the Administrators ACE. Only the service itself and SYSTEM can interact with the process.

Verify the change:

```bash
$ sd show --process $$
Owner:  S-1-5-19 (Local Service)
Group:  S-1-5-19 (Local Service)

DACL:
  Allow  S-1-5-80-2739571183 (DNS Service)  PROCESS_ALL_ACCESS
  Allow  S-1-5-18            (SYSTEM)        PROCESS_ALL_ACCESS
```

## Diagnose process access denials

When a signal or ptrace is denied, use `sd explain`:

```bash
$ sd explain --process 47 3841 PROCESS_VM_READ
Token:   S-1-5-21-...-500 (Administrator)
Object:  process 47 (authd)

[0] PIP dominance check
    Caller PIP:  None
    Target PIP:  Isolated / Trust 4096
    Result:      DENIED — caller does not dominate target

Result: DENIED — PIP dominance required
```

Even though the Administrator would pass the DACL check, PIP blocks the access. No privilege compensates for missing PIP dominance.
