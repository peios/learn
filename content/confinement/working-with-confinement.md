---
title: Working with Confinement
type: how-to
order: 110
---

Confinement state is visible through `idn` and access decisions involving confinement are diagnosable with `sd explain`.

## Inspect a process's confinement state

Confinement information appears in `idn show`:

```
$ idn show 3201
User:         S-1-5-21-...-1013 (alice)
Integrity:    Low
Logon Session: 47291 (Interactive)
Primary:      yes
Confined:     yes
Confinement SID: S-1-15-2-394857203 (MediaPlayer)

Capabilities:
  S-1-15-3-1    internetClient
  S-1-15-3-3    musicLibrary
```

The `Confined` field shows whether confinement is active. The confinement SID identifies the application, and the capabilities list shows what the application declared it needs.

For an unconfined process:

```
Confined:     no
```

## Grant a confined application access to a resource

Objects must explicitly opt in for confined applications to access them. Add an ACE targeting the application's confinement SID or a capability SID:

**Grant access to a specific application:**

```
$ sd add /srv/media/library allow S-1-15-2-394857203 FILE_READ_DATA
```

Only the MediaPlayer application can use this grant. Other confined applications are unaffected.

**Grant access to any application with a specific capability:**

```
$ sd add /srv/media/library allow S-1-15-3-3 FILE_READ_DATA
```

Any confined application that declared the `musicLibrary` capability can read this directory.

**Grant access to all confined applications:**

```
$ sd add /srv/public/shared allow ALL_APPLICATION_PACKAGES FILE_READ_DATA
```

All normal confined applications can read this resource. Strictly confined applications (without ALL_APPLICATION_PACKAGES) are still excluded.

## Diagnose why a confined application was denied

Use `sd explain` to trace the confinement evaluation:

```
$ sd explain /home/alice/.ssh/id_ed25519 3201 FILE_READ_DATA
Token:   S-1-5-21-...-1013 (alice) [confined: S-1-15-2-394857203]
Object:  /home/alice/.ssh/id_ed25519
Request: FILE_READ_DATA

[3] DACL walk (normal evaluation)
    ACE 1: Allow  alice  FILE_ALL_ACCESS
           SID match: yes
           FILE_READ_DATA — granted

[7] Confinement check
    Confinement SID: S-1-15-2-394857203
    Capabilities: S-1-15-3-1, S-1-15-3-3
    DACL walk (confinement evaluation):
      ACE 1: Allow  alice  FILE_ALL_ACCESS
             SID match: no (not a confinement or capability SID) — skip
    Confinement grants: none

Result: DENIED — confinement check denied FILE_READ_DATA
```

The normal evaluation granted access — Alice owns the file. But the confinement check found no ACE targeting the confinement SID or any capability SID. The intersection is empty, so access is denied.

The fix is to either add an ACE for the application's confinement SID to the file, or to not confine the application if it legitimately needs broad access to the user's files.
