---
title: Positive confinement
type: concept
description: A capability SID is just a SID. Where it sits on a token determines what it does. Placed in the normal groups list, the same capability SID that would narrow access in a confined token now grants access through the ordinary DACL walk. This convention — positive confinement — is the canonical pattern in Peios for managing service access at scale.
related:
  - peios/confinement/overview
  - peios/confinement/capabilities-and-modes
  - peios/confinement/the-confinement-pass
  - peios/security-descriptors/dacl-evaluation
  - peios/tokens/token-types
---

**Positive confinement** is a convention, not a kernel feature. It is the practice of taking capability SIDs — the same `S-1-15-3-*` SIDs that name a confinement capability — and placing them in a token's **normal `groups` list** rather than its `confinement_capabilities` list. The kernel does not distinguish capability SIDs from any other SIDs in the groups list; they participate in the ordinary DACL walk like every other group. The result is that the capability acts as a **positive grant** — "this token has this capability, and any ACE that grants rights to this capability grants those rights to this token" — rather than as a confinement constraint.

The name is awkward. "Positive confinement" is not about confinement at all in the access-narrowing sense. It is named after the kind of SID involved (capabilities, which come from the confinement model), with "positive" marking the opposite effect — grant rather than restrict. Once you have the convention in mind it makes sense; on first encounter the name does not help. Reading it as "positive use of capability SIDs" is the cleanest paraphrase.

This page covers what the convention is, why it exists, and how it composes with standard confinement.

## A capability SID is just a SID

The capability SIDs documented in [Capabilities and modes](~peios/confinement/capabilities-and-modes) — `S-1-15-3-1` (`internetClient`), `S-1-15-3-10` (`removableStorage`), and the derived capabilities produced from SHA-256 of capability names — are normal Peios SIDs. They follow the SID format; they compare with byte equality; they appear in ACEs like any other SID; they can be present on a token in any of the SID-bearing fields.

The kernel does not have a "capability SID" type tag. The format does not distinguish them from other SIDs. What makes a capability SID a capability is the namespace convention (`S-1-15-3-*`) and the way administrators choose to use it, not any special handling.

So when you see a capability SID in a token, the question is not "is this a capability". The question is **which field on the token is it sitting in**. The answer is what determines how the access check uses it.

## Placement determines effect

A token has several SID-bearing fields. Two of them are commonly the home of capability SIDs:

| Field | What happens to a capability SID placed here |
|---|---|
| `confinement_capabilities` | The capability is consumed by the **confinement pass** at pipeline step 11. The capability matches ACEs only inside the confinement intersection — its role is to *narrow* what the confined token can reach. |
| `groups` | The capability is consumed by the **normal DACL walk** at pipeline step 8. The capability matches ACEs in the ordinary first-writer-wins evaluation — its role is to *grant* the token whatever rights the ACE specifies. |

Standard confinement uses the first column. Positive confinement uses the second. The same SID, the same DACL, but a very different result.

A token can carry the same capability SID in both fields, or in either, or in neither. The kernel does not check for consistency between the two — the fields are independent.

There are also other SID-bearing fields on the token (the `restricted_sids` list, for example). Capability SIDs are not commonly placed there today, but nothing in the format prevents it; if a future convention emerges, the kernel will treat the SID like any other in that field. The model is open in this respect: a capability SID is reachable by every mechanism that walks any SID list on the token.

## The two effects, compared

A worked-through contrast on the same DACL.

The DACL on a resource contains one ACE:

```
ACCESS_ALLOWED  S-1-15-3-1 (internetClient)  GENERIC_READ
```

**Case 1: token has `internetClient` in `confinement_capabilities`.**

The token's normal identity (user_sid, groups) does not match the ACE, so step 8's DACL walk grants nothing. The token reaches step 11 with an empty grant. The confinement intersection re-walks the DACL against the confinement identity — and the capability list — and finds the ACE matches. The intersection produces a grant of GENERIC_READ-mapped bits. But the running grant from step 8 was empty, so the intersection yields empty too.

Result: **no access**. The capability said "the confined application is permitted to use this resource if its own identity reaches it", and the token's own identity didn't.

**Case 2: token has `internetClient` in `groups`.**

The token's groups include the capability SID. The normal DACL walk at step 8 matches the ACE against the group SID and grants GENERIC_READ-mapped bits. The confinement pass — if even active on this token — re-walks the DACL against `confinement_sid` and `confinement_capabilities`; if the token is not confined, step 11 is a no-op.

Result: **access granted**. The capability acted as a normal group membership — "the token is a member of the internetClient-bearing group, the DACL grants access to that group, the token gets access".

**Case 3: token has `internetClient` in both.**

Step 8 grants because the group SID matches. Step 11 (if confined) re-walks against the confinement identity and finds the same match — the capability is in `confinement_capabilities`, the ACE grants to the capability, the intersection passes. The grant survives.

Result: **access granted**, with the confinement intersection satisfied. This is the pattern when a token is genuinely confined *and* needs to reach a specific capability-gated resource through the confinement layer.

The kernel did the same thing in all three cases — it walked the SIDs it had in the fields it had them in, against the same DACL. The different outcomes are entirely a function of placement.

## Why this convention exists

In a deployment with a handful of services and a few resources, the obvious model is to give each service a dedicated user account and write ACEs naming that user. `jellyfin` reads `/var/lib/jellyfin/`, owned by `jellyfin`, with a DACL granting `jellyfin` full access. Add a new service, create a new user, write new ACEs.

At any kind of scale this breaks down. A dozen services each touching a few dozen shared resources is hundreds of ACE entries to maintain, and every new service requires editing the DACL of every resource it touches. Service accounts become a sprawl of `nobody`-style entries that exist only to appear in ACL lists.

Positive confinement is the alternative pattern. Instead of:

- A `jellyfin` user, mentioned in every media-file DACL.
- A `transmission` user, mentioned in every download-directory DACL.
- A `nextcloud` user, mentioned in every shared-storage DACL.

You define **capabilities** — semantic units of access — and grant ACEs to *those*:

- A `media-library-read` capability. Every media file's DACL grants `GENERIC_READ` to this capability.
- A `download-write` capability. Every download directory's DACL grants `GENERIC_WRITE` to this capability.
- A `shared-storage` capability. Every shared-storage object's DACL grants to this capability.

Then each service is given the capabilities it needs as entries in its token's groups. Adding a new media-handling service does not require modifying every media file's DACL — the DACL already grants `media-library-read`; the new service just needs the capability on its token.

The administrative model becomes: services consume capabilities; resources grant capabilities; the directory maintains which services have which capabilities. ACLs on shared resources are stable. Adding a service is a token-policy change, not a DACL-rewriting exercise.

This is what positive confinement is *for*. Most non-trivial Peios deployments use it. Dedicated service accounts continue to exist for cases where the per-service identity is genuinely meaningful (a service whose data should be exclusively its own), but for shared resources reached by multiple services, capability-style positive grants are the canonical pattern.

## Positive confinement does not bypass confinement

This is the most important rule about composition and it is worth saying directly: **positive confinement does not bypass confinement**. If a token is confined, putting a capability SID in the token's `groups` does not exempt the resulting access from the confinement pass at step 11. The DACL walk at step 8 may grant rights through the capability appearing in groups, but the confinement intersection still runs, and if the confinement identity (`confinement_sid` plus `confinement_capabilities`) does not match the same ACE, the grant is dropped.

The kernel does not look at the SID and reason about its "intent". It runs each pipeline step with the inputs that step uses. Step 8 uses the token's `groups`. Step 11 uses the token's `confinement_capabilities`. A capability SID present in one but not the other satisfies one step but not the other, and an intersection that fails at any active step removes the rights.

Practically: on a confined token, positive confinement and standard confinement are **complementary, not alternatives**. To reach an object via a capability, both halves need to be in place:

- The capability SID in `groups`, so the normal DACL walk at step 8 grants access.
- The capability SID also in `confinement_capabilities`, so the confinement intersection at step 11 preserves the grant.

Either half on its own grants the confined token nothing. Putting the capability only in `groups` produces a step-8 grant that step 11 strips. Putting it only in `confinement_capabilities` keeps step 11 happy but step 8 grants nothing for the intersection to preserve.

The pattern, then, on a confined service's token: the same capability SID appears in both places. The DACL grants to the capability; the token bears it twice; both checks pass.

For tokens that are **not** confined — which is many of them, especially in standalone or smaller deployments — only the `groups` half matters. The confinement pass is a no-op for an unconfined token; the normal DACL walk is the only check that runs against the capability. This is the "positive confinement without confinement" case: the capability SIDs are used as ordinary groups for access management, and the confinement layer never enters the picture.

## What this is *not*

A few clarifications, because the name encourages misreading:

- **It is not a bypass of confinement.** Placing a capability SID in a confined token's `groups` does not exempt the resulting access from step 11. The confinement pass still fires; the grant from the DACL walk is still subject to the intersection. See "Positive confinement does not bypass confinement" above.
- **It is not a separate access-check pass.** There is no "positive confinement evaluator" in the kernel. The DACL walk at step 8 finds the capability SID like it finds any other group SID. No new mechanism, no new code path, no special handling.
- **It is not the same as confinement.** A token with capability SIDs only in groups (no `confinement_sid`) is **not confined**. The confinement pass is a no-op. The token has the broad access its identity grants; the capabilities sit alongside as additional group memberships.
- **It is not opt-in for the resource.** A resource whose DACL grants access to a capability does not need to know whether the caller is using the capability positively or as a confinement entry. The DACL says "this SID gets these rights"; whoever has the SID in a relevant field gets the access.
- **It is not a kernel feature you can disable.** Because there is no feature flag — only a convention about where you put capability SIDs on tokens — there is nothing to turn off. Sites that prefer dedicated service accounts simply do not use capability SIDs in groups.

## A worked deployment

A Peios machine runs three services that all read the user's music library: `jellyfin`, `mpd`, and a future `streaming-bridge`. The administrative pattern is positive confinement.

The DACL on `/var/lib/media/music/` (and every file under it):

- `ACCESS_ALLOWED  SYSTEM  GENERIC_ALL`
- `ACCESS_ALLOWED  BUILTIN\Administrators  GENERIC_ALL`
- `ACCESS_ALLOWED  music-library-read  GENERIC_READ`  *(the capability SID, derived from "music-library-read" via SHA-256)*

The directory policy in authd configures each service's token to include the `music-library-read` capability SID in its `groups`:

- `jellyfin`'s token: `groups = [jellyfin_user_SID, music-library-read, network-server, ...]`
- `mpd`'s token: `groups = [mpd_user_SID, music-library-read, audio-output, ...]`
- `streaming-bridge`'s token: `groups = [streaming-bridge_user_SID, music-library-read, network-server, ...]`

Each service is a different user identity. Each service has the capability through its groups. Each service can read the music library.

The administrator adds a fourth music-handling service. The new service's token policy includes `music-library-read` in groups. The DACL on `/var/lib/media/music/` is not touched. The service starts reading the library immediately.

If the deployment additionally confines the services for sandboxing, the same capability SID also appears in each service's `confinement_capabilities`. The DACL ACE for `music-library-read` is unchanged. The token now has the SID in two places, and both passes find it. Access still works.

This is the canonical scale pattern. Capabilities are the vocabulary of access; tokens consume capabilities; resources grant capabilities; administrative policy decides who gets what. No DACL rewrites when new services arrive; no proliferation of per-service users in every shared-resource ACL.
