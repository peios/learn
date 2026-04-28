---
title: Working with Process Silos
type: how-to
description: Inspecting silo membership, granting siloed processes access to resources, and diagnosing silo-related access denials.
related:
  - peios/process-silos/understanding-process-silos
  - peios/process-silos/namespaces
  - peios/confinement/working-with-confinement
---

Process silo state is visible through `idn` and access decisions involving silos are diagnosable with `sd explain`. The tools are the same ones used for confinement — silo SIDs simply appear in different places.

## Inspect a process's silo state

Silo information appears in `idn show`:

```bash
$ idn show 8492
User:         S-1-5-21-...-1055 (jellyfin)
Integrity:    System
Logon Session: 47812 (Service)
Primary:      yes
Confined:     no

Silo SID:     S-1-5-1515-1-849273-23847-12384-99381 (jellyfin-instance-01)
Silo Capabilities:
  S-1-15-3-1    internetClient
  S-1-15-3-3    privateNetworkClientServer
  S-1-15-2-1    ALL_APPLICATION_PACKAGES

Namespaces:
  PID:       S-1-5-1515-2-...    (silo-private)
  Network:   S-1-5-1515-3-...    (silo-private)
  Mount:     S-1-5-1515-4-...    (silo-private)
  IPC:       S-1-5-1515-5-...    (host-shared)
  Hostname:  S-1-5-1515-6-...    (host-shared)
  Cgroup:    S-1-5-1515-7-...    (silo-private)
  Time:      S-1-5-1515-8-...    (host-shared)
```

The `Silo SID` field shows which silo the process is in. The capability list shows what the silo declared at creation. The namespaces section shows which namespaces are silo-private vs shared with the host.

For a process not in a silo:

```
Silo SID:     none
```

## Grant a siloed process access to a resource

Objects must explicitly opt in for siloed processes to access them, just like confinement. Add an ACE targeting one of the silo's identity elements.

**Grant access to a specific silo:**

```bash
$ sd add /var/lib/jellyfin/library allow S-1-5-1515-1-849273-23847-12384-99381 FILE_READ_DATA
```

Only this specific silo can use this grant.

**Grant access to any silo or confined process with a specific capability:**

```bash
$ sd add /var/lib/jellyfin/library allow S-1-15-3-3 FILE_READ_DATA
```

Any siloed or confined process declaring `privateNetworkClientServer` can read this directory.

**Grant access to all non-strict silos and confined processes:**

```bash
$ sd add /srv/public allow ALL_APPLICATION_PACKAGES FILE_READ_DATA
```

All non-strict siloed and confined processes can read this resource.

The capability and well-known SID vocabulary is shared between confinement and silos. An ACE granting `internetClient` is reachable from siloed processes the same way it is reachable from confined applications.

## Grant access to a specific namespace

Namespace SIDs can also appear directly in DACLs:

```bash
$ sd add /var/log/network allow S-1-5-1515-3-849273-23847-12384-99381 FILE_READ_DATA
```

Any process in this network namespace gains read access. This is independent of silos — a process not in any silo, but in this network namespace, would still match.

This is useful for granting per-namespace access without requiring the namespace to be wrapped in a silo, but it ties the ACL to a specific namespace instance whose SID changes if the namespace is recreated (or across reboots for the host's namespaces).

## Diagnose why a siloed process was denied

Use `sd explain` to trace the silo evaluation:

```bash
$ sd explain /etc/peios/registry/secrets 8492 FILE_READ_DATA
Token:   S-1-5-21-...-1055 (jellyfin)
PSB:     silo S-1-5-1515-1-849273-23847-12384-99381 (jellyfin-instance-01)
Object:  /etc/peios/registry/secrets
Request: FILE_READ_DATA

[3] DACL walk (normal evaluation)
    ACE 1: Allow  jellyfin  FILE_ALL_ACCESS
           SID match: yes
           FILE_READ_DATA — granted

[8] Silo check
    Silo SID: S-1-5-1515-1-849273-23847-12384-99381
    Capabilities: S-1-15-3-1, S-1-15-3-3, S-1-15-2-1
    DACL walk (silo evaluation):
      ACE 1: Allow  jellyfin  FILE_ALL_ACCESS
             SID match: no (not silo or capability SID) — skip
    Silo grants: none

Result: DENIED — silo check denied FILE_READ_DATA
```

The normal evaluation granted access — the jellyfin user owns the file. But the silo check found no ACE targeting the silo SID, any capability SID, or `ALL_APPLICATION_PACKAGES`. The intersection is empty, so access is denied.

The fix is to add an ACE granting the silo's specific SID, one of its capabilities, or `ALL_APPLICATION_PACKAGES` (if appropriate for the resource).

## Combine silos with confinement

A process can be both confined (token level) and siloed (process level). Both checks run independently and both must pass:

```bash
$ idn show 9201
User:         S-1-5-21-...-1080 (alice)
Integrity:    Low
Logon Session: 47291 (Interactive)
Primary:      yes
Confined:     yes
Confinement SID: S-1-15-2-394857203 (MediaPlayer)
Confinement Capabilities:
  S-1-15-3-3    musicLibrary

Silo SID:     S-1-5-1515-1-...-... (mediaplayer-instance)
Silo Capabilities:
  S-1-15-3-3    musicLibrary
```

For this process to access an object, the DACL must grant the right via:

1. The normal walk (Alice's user SID, groups)
2. The confinement intersection (matching `S-1-15-2-394857203`, `musicLibrary`, or `ALL_APPLICATION_PACKAGES`)
3. The silo intersection (matching the silo SID, `musicLibrary`, or `ALL_APPLICATION_PACKAGES`)

All three must independently grant the requested rights. The intersection of three masks is what survives.

## Common mistakes

**Adding capability SIDs to the wrong slot.** A capability SID in the silo capabilities set is restrictive (silo intersection); the same SID in the token's groups set is additive ([positive confinement](../confinement/positive-confinement)); the same SID in the token's confinement capabilities is restrictive at the token level. Where the SID lives changes its effect entirely.

**Expecting silos to provide resource limits.** A siloed process can still consume host CPU and memory. Apply resource limits separately.

**Assuming `ALL_APPLICATION_PACKAGES` is enough.** It works for many system objects that broadly opt in, but for service-specific resources, the silo SID or capability SIDs are usually required.

**Trying to escape a silo by entering a foreign namespace.** Entering a namespace outside the current silo is denied. Once a process is in a silo, the silo is the only way out — exit, and a new process can be started elsewhere.
