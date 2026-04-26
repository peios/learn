---
title: Working with Positive Confinement
type: how-to
description: Granting a service cross-service access using capability SIDs as group memberships, and inspecting the result.
related:
  - peios/confinement/positive-confinement
  - peios/confinement/working-with-confinement
---

Positive confinement uses capability SIDs as group memberships rather than confinement capabilities. The tools are the same ones used for confinement — `idn` and `sd` — but the SIDs appear in different places.

## Identify the capability you need

Find the capability SID that the target resource already grants to. Use `sd show` on the resource:

```bash
$ sd show /run/dns/control.sock
Owner: S-1-5-21-...-1040 (dns-service)
DACL:
  Allow  S-1-5-21-...-1040       SOCKET_READ | SOCKET_WRITE
  Allow  S-1-15-3-8472           SOCKET_WRITE              # modifyDns capability
  Allow  ALL_APPLICATION_PACKAGES SOCKET_READ
```

The `modifyDns` capability (`S-1-15-3-8472`) is already on the socket for confined applications. This is the SID you will use as a group membership.

## Grant the capability as a group membership

Add the capability SID to the service's token as a group membership. How you do this depends on how the service is launched — the SID is added to the token at creation time, not at runtime.

For a service managed by peinit:

```bash
$ loreg set HKLM\System\Services\dhcpd\Security\AdditionalGroups \
    S-1-15-3-8472
```

When peinit next starts the DHCP service, the `modifyDns` capability SID will appear in the token's groups set.

## Inspect the result

Use `idn show` on the running service to verify the SID placement:

```bash
$ idn show 4810
User:         S-1-5-21-...-1055 (dhcpd)
Integrity:    System
Logon Session: 2 (Service)
Primary:      yes
Confined:     no

Groups:
  S-1-5-21-...-1055    dhcpd
  S-1-5-11             Authenticated Users
  S-1-15-3-8472        modifyDns           # ← capability as a group
```

The `modifyDns` SID is in the **Groups** list, not in a Capabilities list. The process is not confined. The SID will participate in the normal DACL walk.

Compare this with a confined process that carries the same capability:

```bash
$ idn show 5102
User:         S-1-5-21-...-1061 (dns-updater-app)
Integrity:    Low
Logon Session: 47291 (Interactive)
Primary:      yes
Confined:     yes
Confinement SID: S-1-15-2-990124 (DnsUpdater)

Capabilities:
  S-1-15-3-1           internetClient
  S-1-15-3-8472        modifyDns           # ← capability in confinement set
```

Same SID, different placement, different access check behavior.

## Verify access with sd explain

Use `sd explain` to confirm that the positive confinement grant works as expected:

```bash
$ sd explain /run/dns/control.sock 4810 SOCKET_WRITE
Token:   S-1-5-21-...-1055 (dhcpd)
Object:  /run/dns/control.sock
Request: SOCKET_WRITE

[3] DACL walk (normal evaluation)
    ACE 1: Allow  dns-service  SOCKET_READ | SOCKET_WRITE
           SID match: no — skip
    ACE 2: Allow  S-1-15-3-8472  SOCKET_WRITE
           SID match: yes (group membership)
           SOCKET_WRITE — granted

[7] Confinement check
    Token is not confined — skipped

Result: GRANTED — SOCKET_WRITE
```

The normal DACL walk matched the capability SID as a group membership. No confinement check was involved.

## Diagnose a common mistake

If you accidentally add the capability SID to a confined token's groups set instead of its confinement capabilities set, the confinement check will deny access even though the normal DACL walk succeeds:

```bash
$ sd explain /run/dns/control.sock 5200 SOCKET_WRITE
Token:   S-1-5-21-...-1070 (misconfigured-app) [confined: S-1-15-2-443210]
Object:  /run/dns/control.sock
Request: SOCKET_WRITE

[3] DACL walk (normal evaluation)
    ACE 2: Allow  S-1-15-3-8472  SOCKET_WRITE
           SID match: yes (group membership)
           SOCKET_WRITE — granted

[7] Confinement check
    Confinement SID: S-1-15-2-443210
    Capabilities: S-1-15-3-1
    DACL walk (confinement evaluation):
      ACE 2: Allow  S-1-15-3-8472  SOCKET_WRITE
             SID match: no (not in confinement capabilities) — skip
    Confinement grants: none

Result: DENIED — confinement check denied SOCKET_WRITE
```

The SID was in the groups set, so the normal walk found it. But the confinement check only looks at the confinement capabilities set, where the SID was absent. The intersection is empty.

The fix: add the SID to the token's confinement capabilities set if the process is confined, or use it as a group membership only on unconfined tokens.
