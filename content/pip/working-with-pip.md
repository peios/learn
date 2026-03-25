---
title: Working with PIP Protection
type: how-to
order: 110
---

PIP information surfaces through the same tools used for identity and security descriptors.

## Check a process's PIP level

PIP type and trust level are shown in `idn show`:

```
$ idn show 1482
User:         S-1-5-19 (Local Service)
Integrity:    System
Logon Session: 3 (Service)
Primary:      yes
PIP:          Protected / Trust 2048 (Peios)

Groups:
  ...
```

The `PIP` line shows the type (Isolated, Protected, or None) and the trust level with its signer name.

For unprotected processes, it shows:

```
PIP:          None
```

## List PIP-protected processes

Use `idn list --pip` to see all PIP-protected processes on the system:

```
$ idn list --pip
PID     User                      PIP                         Binary
1       S-1-5-18 (SYSTEM)         Isolated / Trust 4096       /sbin/peinit
47      S-1-5-18 (SYSTEM)         Isolated / Trust 4096       /usr/lib/peios/authd
52      S-1-5-18 (SYSTEM)         Protected / Trust 4096      /usr/lib/peios/loregd
61      S-1-5-18 (SYSTEM)         Protected / Trust 4096      /usr/lib/peios/eventd
```

## Identify PIP-protected files

Trust label ACEs appear in the SACL when you inspect an object's security descriptor:

```
$ sd show /usr/lib/peios/authd
Owner:  S-1-5-18 (SYSTEM)
Group:  S-1-5-18 (SYSTEM)

DACL:
  Allow  S-1-5-18 (SYSTEM)           FILE_ALL_ACCESS
  Allow  S-1-5-32-544 (Administrators)  FILE_READ_DATA | FILE_READ_ATTRIBUTES | READ_CONTROL

SACL:
  Trust Label: Protected / Trust 2048  (restrict: write, execute)
```

The trust label shows the minimum PIP level required and which access categories are restricted. In this example, only processes at Protected with trust 2048 or higher can write to or execute this binary. Read access is unrestricted by PIP (though the DACL still controls who can read).

## Understand why PIP blocked access

When access is denied due to PIP, `sd explain` shows it:

```
$ sd explain /usr/lib/peios/authd 3841 FILE_WRITE_DATA
Token:   S-1-5-21-...-500 (Administrator)
Object:  /usr/lib/peios/authd
Request: FILE_WRITE_DATA

[1] PIP trust label check
    Process PIP:    None
    Trust label:    Protected / Trust 2048 (restrict: write, execute)
    FILE_WRITE_DATA is restricted
    Result:         DENIED — caller does not dominate trust label

Result: DENIED — PIP trust label
```

The administrator has no PIP protection (running an unsigned binary), so they cannot write to the trust-labeled file — despite being an administrator with a DACL that would otherwise grant access.

For process access denials, the error is reported directly:

```
$ idn show 47
Error: access denied — PIP dominance required (target: Isolated / Trust 4096)
```

The error tells you the target's PIP level, making it clear what level of protection you would need to access it.
