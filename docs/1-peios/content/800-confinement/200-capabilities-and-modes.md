---
title: Capabilities and modes
type: concept
description: A confined application declares what it can reach as a set of capability SIDs. Each capability names a kind of resource. This page covers the structure of capability SIDs, the well-known capabilities, derived capabilities, and the difference between normal and strict confinement modes.
related:
  - peios/confinement/overview
  - peios/confinement/the-confinement-pass
  - peios/confinement/positive-confinement
  - peios/identity/well-known-principals
---

A confined application's reach is expressed as a list of **capability SIDs** on its token. Each capability is a named permission to use a kind of resource: network access, removable storage, the certificate store. The kernel matches the capability list against ACEs in the DACLs of objects the application touches; an ACE granting access to a capability the confined application has declared lets the access through, while objects whose DACLs do not mention any declared capability are unreachable.

This page covers the capability SID format, the well-known capabilities, how custom capabilities are derived from names, and the two confinement modes (normal and strict).

## What a capability SID looks like

All capability SIDs sit under the `S-1-15-3-*` namespace. There are two flavours:

- **Well-known capabilities** have small numeric sub-authorities (`S-1-15-3-1`, `S-1-15-3-2`, etc.) assigned to specific named permissions.
- **Derived capabilities** have eight sub-authorities computed from the SHA-256 hash of the capability name. The same name always produces the same SID. The hash is split into eight little-endian 32-bit values and appended to `S-1-15-3-`.

The format itself does not distinguish the two. They are both `S-1-15-3-...`-shape SIDs; the access check matches them as plain SIDs.

## The well-known capabilities

| SID | Capability |
|---|---|
| `S-1-15-3-1` | `internetClient` — outbound internet access. |
| `S-1-15-3-2` | `internetClientServer` — inbound and outbound internet. |
| `S-1-15-3-3` | `privateNetworkClientServer` — LAN / private network access. |
| `S-1-15-3-8` | `enterpriseAuthentication` — domain credential access. |
| `S-1-15-3-9` | `sharedUserCertificates` — certificate store access. |
| `S-1-15-3-10` | `removableStorage` — removable media access. |

The SIDs at positions 4 through 7 are reserved and not used in v0.20. The well-known capability set is deliberately small — every additional well-known capability has to be defined globally and means the same thing on every Peios system. Capabilities specific to one application or one environment use the derived form.

The way these SIDs become meaningful is the same as any other SID: they appear in ACEs on objects whose DACLs grant access to them. The system's network stack, for example, has SDs on its endpoints that grant access to `internetClient`; a confined application carrying `internetClient` as a capability can reach those endpoints; one without it cannot. The capability SID is the link between the policy on the resource and the declaration on the token.

## Derived capabilities

For capabilities specific to an application or a deployment, the SID is derived from a string:

```
S-1-15-3-{h0}-{h1}-{h2}-{h3}-{h4}-{h5}-{h6}-{h7}
```

The eight 32-bit values come from `SHA-256(name)`, split into eight 32-bit little-endian integers in order. The same name always produces the same SID. Two different names (even names that differ in a single character) produce different SIDs with overwhelming probability — SHA-256's collision resistance does the work.

A derived capability is meaningful when:

1. The application's manifest declares the capability by name, so authd can compute the SID and put it on the token.
2. The resources the capability protects have DACLs containing ACEs that grant rights to the same SID.

Both ends use the same derivation, so they meet at the same SID. The string name is human-readable convention; the kernel only ever sees the derived SID.

Derived capabilities are how an application-vendor or system integrator extends the model without coordinating with the OS. An application that needs access to a vendor-specific resource declares a vendor-specific capability name; the vendor's installer arranges for the resource's DACL to grant that capability; the two sides agree implicitly through the SHA-256 derivation.

## Confinement modes — normal vs strict

The well-known SID `ALL_APPLICATION_PACKAGES` (`S-1-15-2-1`) and the related `ALL_RESTRICTED_APPLICATION_PACKAGES` (`S-1-15-2-2`) define the two confinement modes. These are not capabilities themselves — they are matchers used in ACEs to grant access to *all* confined applications, or to confined applications in strict mode.

| Confinement mode | `ALL_APPLICATION_PACKAGES` matches the token? | `ALL_RESTRICTED_APPLICATION_PACKAGES` matches? |
|---|---|---|
| **Normal** | Yes | Yes |
| **Strict** | **No** | Yes |

The difference: an ACE granting rights to `ALL_APPLICATION_PACKAGES` lets every confined application reach the object in normal mode, but **not** strict-mode applications. An ACE granting rights to `ALL_RESTRICTED_APPLICATION_PACKAGES` lets confined applications in both modes through.

The mode is a property of the token at creation. It is encoded by whether `ALL_APPLICATION_PACKAGES` appears as one of the token's `confinement_capabilities`:

- If `ALL_APPLICATION_PACKAGES` (`S-1-15-2-1`) is **present** in the token's confinement capabilities → normal mode.
- If it is **absent** → strict mode.

Token construction rejects tokens that try to carry `ALL_APPLICATION_PACKAGES` as a capability **in strict-mode tokens** (any non-strict combination is fine).

The practical effect of strict mode: a strict-mode application can reach only objects whose DACLs explicitly grant access to its capabilities or to `ALL_RESTRICTED_APPLICATION_PACKAGES`. The much larger set of objects that grant to `ALL_APPLICATION_PACKAGES` are off-limits.

This is what "strict" means. Most operating-system resources whose policy grants broad access to confined applications use `ALL_APPLICATION_PACKAGES`; a strict application is choosing to opt out of those broad grants and rely only on its specific named capabilities.

When to choose strict over normal: when the application's threat model says it should not be able to reach resources whose authors granted broad access without specifically intending to include it. The trade-off is operational — strict applications often need their own specific capability grants on every resource they need, which is more work.

## Capability matching during the confinement pass

When the confinement pass (pipeline step 11) re-walks the DACL against the confinement identity, the matching rule is:

- The token's `confinement_sid` matches an ACE whose SID is the same.
- Each entry in `confinement_capabilities` matches an ACE whose SID is the same.
- `ALL_APPLICATION_PACKAGES` matches an ACE on that SID **only if** the token's capabilities include it (i.e. only in normal mode).
- `ALL_RESTRICTED_APPLICATION_PACKAGES` matches an ACE on that SID **always**, in both modes.
- Group attributes on the token's capabilities are **ignored**. The capability list is presence-based — what matters is whether a SID appears, not what its enabled/disabled state is.

The matching is bare SID equality. The capability identity does not carry a privilege bitmask, group membership semantics, or anything else. It is just a SID that names a kind of resource.

The full mechanics of the pass — what gets intersected, what bypasses — are in [The confinement pass](~peios/confinement/the-confinement-pass).

## Capability declaration vs grant

A small but important distinction: declaring a capability is **not** the same as having access to the resources it names.

A token's `confinement_capabilities` is the list of capabilities the confined application is *allowed* to use. Whether it actually gets access to a specific object still depends on the object's DACL — the capability SID has to appear in an allow ACE.

If a token declares `internetClient` but no network resource has an ACE granting `internetClient` rights, the capability declaration achieves nothing. Conversely, if a token does **not** declare `internetClient` but some objects have ACEs granting access to that SID, the confined application still cannot reach them — the capability has to be on the token *and* the ACE has to grant access to it.

The model is conjunctive: both the token-side declaration and the resource-side grant have to agree. Capabilities are a vocabulary; the DACLs are the actual permissions. Without both halves the access does not happen.

This page describes the declaration half — the appearance of capability SIDs in `confinement_capabilities`, where they are consumed by the confinement pass. Capability SIDs can also appear in a token's `groups` list, where they are consumed by the ordinary DACL walk and act as positive grants rather than confinement constraints. That convention — [positive confinement](~peios/confinement/positive-confinement) — is how most non-trivial Peios deployments express service access. The capability vocabulary is the same; the placement on the token decides which mechanism uses it.

## Capabilities and other narrowing layers

Capabilities live in the confinement pass. They do not appear in:

- The normal DACL walk (step 8). The DACL walk uses the token's `user_sid` and `groups`, not its `confinement_capabilities`. Capabilities are invisible to step 8.
- The restricted-token pass (step 10). Restricted tokens narrow against `restricted_sids`, not against capabilities. A restricted-and-confined token gets both intersections.
- CAAP evaluation (step 12). Central access policies do not match capabilities specifically; they match the token's normal SIDs.

The capability SID is only used in step 11. If you are writing an ACE that grants access to a capability, that ACE will only be relevant when a confined token is the caller. For a non-confined token, the ACE is just an entry with a SID nothing in the token matches.

## Practical pattern: granting access to a capability

A typical SD on a resource intended to be reachable by confined applications might look like:

- An ACE granting `BUILTIN\Administrators` `GENERIC_ALL`. (Administrative full control.)
- An ACE granting `SYSTEM` `GENERIC_ALL`. (System full control.)
- An ACE granting `Authenticated Users` `GENERIC_READ`. (Standard authenticated read.)
- An ACE granting `internetClient` `FILE_READ_DATA | FILE_WRITE_DATA`. (Confined applications with the internetClient capability can use it.)

A non-confined token reaches the resource through its normal identity (Authenticated Users, administrative groups, etc.). A confined token additionally needs the capability ACE to match a SID in its `confinement_capabilities` for the confinement pass to leave the access intact. The two sides — normal identity for the DACL walk, capability for the confinement pass — both have to grant.

The presence of capability ACEs on system resources is what makes confined applications usable in practice. Without them, every confined application would be locked out of everything that did not specifically know about it.
