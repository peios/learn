---
title: Capability Policy
type: concept
description: Distinguish capability grants from confinement and plan the token and resource sides together.
---

A capability SID names an audience for access policy. Its effect depends on
where the token carries it, not on its name. A capability called
`internetClient` does not itself intercept network traffic or grant a socket.
An enforcing object manager and matching resource policy must exist.

## Grants and confinement

| Token field | Effect of a capability SID |
|---|---|
| Ordinary groups | Participates in the normal DACL walk, subject to group attributes. |
| Confinement capabilities | Participates in the additional confinement intersection when that pass is active. Presence matters; disabling a capability does not remove it from that identity. |
| Both | Can satisfy both walks, but does not bypass any other access restriction. |

Using capability SIDs in ordinary groups is sometimes called *positive
confinement*. It is an administrative convention for grants, not a sandbox.
It does not remove unrelated rights, privileges, or existing handles.

For example, a media library can grant read access to a `media-library-read`
SID. An administrator can arrange for approved service tokens to carry that
SID as an enabled group, without listing every service account in every
file's DACL. A service given that SID only in its confinement capabilities
still needs its ordinary identity to obtain the read grant. An intersection
cannot create rights missing from the first walk.

Keep the account, token-creation policy, and object grants distinct. Changing
a policy document does not update an already-created token. Verify the
launcher's actual token construction rather than assuming an application
manifest is automatically interpreted by authd.

## Confinement as a second check

An active confinement pass intersects the existing grant with the rights
justified by the confinement SID and capability list. Backup and restore
privilege grants do not escape that intersection. Owner implicit rights are
not added by the confinement walk. A null DACL still means no discretionary
restriction, so confinement is not an unconditional deny-by-default wrapper
around every object.

A library file can therefore grant ordinary read access to the service's
account and confinement read access to its package SID. The service can read
it but cannot change its DACL merely because the account owns it. Granting a
capability alone cannot overcome MIC, PIP, central policy, or a denial in the
ordinary walk.

Normal confinement includes `ALL_APPLICATION_PACKAGES`; strict confinement
omits it and consequently does not match broad grants to that SID. These
are supplied SID sets, not a separate mode flag. Supply every intended
capability explicitly. The [kernel confinement
reference](~kernel/internals/kacs/access-check/application-confinement)
defines virtual groups, conditional expressions, null DACLs, and ordering.

Confinement constrains AccessCheck-mediated operations. It does not remove
standalone kernel privileges, isolate namespaces, make inaccessible objects
invisible, or retroactively revoke transferred file handles. Treat the
reserved isolation-boundary field as unavailable functionality.

## Naming and deploying capabilities

The capability namespace is `S-1-15-3-*`. Well-known names include network,
enterprise authentication, certificate-store, and removable-storage
capabilities. Custom names use the defined SHA-256 derivation: eight
little-endian 32-bit subauthorities after `S-1-15-3`. Use the same exact name
and derivation on the token and resource sides. The
[package specification](~specifications/pspu/package-format-and-repository-protocol/derived-capabilities)
owns the encoding; a recognizable name is not evidence of enforcement.

Before deploying a capability-based service:

1. Identify each resource and required operation, including startup,
   maintenance, and recovery paths.
2. Inspect ordinary groups, privileges, confinement identity, and inherited
   descriptors independently. A confinement exemption skips that pass.
3. Arrange explicit grants on the resources and explicit token creation by
   the launcher. Keep a separate authorized management path.
4. Test both permitted and refused operations with fresh handles. Test
   failures without granting broad fallback access.
5. Recheck a replacement process after policy changes. Record the policy and
   deployed identities so the result can be reproduced.

Restricted tokens offer a different way to narrow authority inside a program.
They can coexist with confinement, but their privilege-restoration rules
are different. See [restricted
tokens](~kernel/internals/kacs/access-check/restricted-tokens).
