---
title: Access control on keys
type: concept
description: "Every registry key is a secured object, governed by the same KACS access check as files, processes, and tokens — checked once at open, cached on the handle. This page covers the registry-specific rights, the surprises (no traversal check; access is per key, not per value), and the sharp interaction with layers: a security change is not reverted when a layer is removed."
related:
  - peios/registry/layers
  - peios/registry/watches
  - peios/security-descriptors/overview
  - peios/access-decisions/overview
  - peios/file-access/the-handle-model
---

Every registry key is a secured object. It carries a [security descriptor](~peios/security-descriptors/overview) — owner, DACL, and optionally a SACL — exactly like a file, a process, or a token. And the registry does not invent its own access logic: opening a key runs the same [AccessCheck](~peios/access-decisions/overview) pipeline that governs every other protected object in Peios, against the same tokens and the same SD format. If you understand access control for files, you already understand most of it for the registry.

## Access control on keys, in one sentence

**Every key carries a security descriptor, and access to it is decided by the same AccessCheck that governs everything else — evaluated once when you open the key, then cached on the handle for the life of that handle.**

## Security is per key, not per value

A security descriptor lives on the **key**. Values do not have their own — they inherit their key's access control. "Who can read this value, who can change it" is answered by the SD on the key that contains it, and there is no finer-grained permission than that. If two values need different access rules, they belong in different keys.

## The handle model

Access is checked at **open**, not on every operation. When you open a key for some set of rights, AccessCheck runs once; if it grants them, you get a key handle (a file descriptor) with a **granted access mask** baked in. Every later operation through that handle is a cheap bitmask check against the cached mask — *is this operation's required right in what I was granted?* — not a fresh AccessCheck.

The consequence is the same **check-at-open** rule that [files](~peios/file-access/the-handle-model) and [central access policies](~peios/central-access-policies/overview) follow: changing a key's SD affects *future* opens, not handles that are already open. An administrator who tightens a key's DACL does not retract access from a service that already has the key open — the recourse is to make the service reopen (typically by restarting it). The handle is a snapshot of the decision made at open time.

## The registry-specific rights

A key's DACL is written in terms of rights specific to keys:

| Right | Gates |
|---|---|
| `KEY_QUERY_VALUE` | Reading values. |
| `KEY_SET_VALUE` | Writing and deleting values. |
| `KEY_CREATE_SUB_KEY` | Creating child keys. |
| `KEY_ENUMERATE_SUB_KEYS` | Listing child keys. |
| `KEY_NOTIFY` | Arming a [watch](~peios/registry/watches). |
| `KEY_CREATE_LINK` | Creating a [link key](~peios/registry/registry-links) (privileged). |
| `DELETE` | Deleting the key, or hiding it in a layer. |
| `READ_CONTROL` | Reading the SD and key metadata. |
| `WRITE_DAC` / `WRITE_OWNER` | Changing the DACL / the owner. |
| `ACCESS_SYSTEM_SECURITY` | Reading or changing the SACL (audit policy). |

The usual convenience bundles apply — `KEY_READ` (query, enumerate, notify, read the SD), `KEY_WRITE` (set values, create subkeys), and `KEY_ALL_ACCESS`.

Ordinary access — reading a value, writing one, creating or listing subkeys — is decided entirely by the key's SD through AccessCheck. **No privilege grants ordinary registry access.** A few privileges appear only where a write means more than storage: establishing a layer that *outranks* others (policy — see [Layers](~peios/registry/layers)), creating a link, or bulk [backup and restore](~peios/registry/lcs-and-sources). Those are special operations, covered where they arise; everyday access is the SD's job alone.

## No traversal check

One surprise sets the registry apart from a filesystem: **only the SD on the key you open is checked.** The keys above it on the path are not. A process can open `Machine\System\Services\Jellyfin` with no access whatsoever to `Machine\System\Services` or `Machine\System`. There is no "execute/traverse" right that you must hold on every ancestor the way a filesystem demands. Access is decided at the destination, full stop.

This matters when you reason about exposure: locking down a parent key does **not** lock down what is beneath it. If a subtree must be protected, the protection has to be on the keys that hold the data, not merely on a key somewhere above them.

## Where a key's SD comes from

A key's SD is computed **once, at creation**, by inheriting from its parent — the same eager, static [inheritance](~peios/security-descriptors/inheritance) files use. It is then a complete value stored on the key; the parent is not consulted again at access time. Changing a parent's SD does **not** ripple down to children that already exist — re-applying inheritance to an existing subtree is a deliberate administrative walk, not something that happens on its own.

The chain has to start somewhere, and it starts at the hive roots, whose SDs are the seeds for everything below:

| Hive root | Default access |
|---|---|
| `Machine\` | SYSTEM and Administrators: full control. Authenticated Users: read. (All inheritable.) |
| `Users\<SID>\` | That user, SYSTEM, and Administrators: full control. |

Subsystems that need something tighter than "Authenticated Users can read" set an explicit SD on their own subtree root at creation, overriding the inherited default for everything beneath it.

## Watching requires permission to read

Arming a [watch](~peios/registry/watches) needs `KEY_NOTIFY`, so a process cannot monitor a key it could not otherwise observe. One deliberate asymmetry: a *subtree* watcher learns that a descendant key was created or deleted — structural facts — without holding any access to that descendant. It learns that something appeared; it must still open it (and pass AccessCheck) to read what is inside. Structure visibility is intentionally weaker than content visibility.

## The sharp edge: security is not layered

This is where the registry's two big ideas meet, and the result surprises people. [Layers](~peios/registry/what-layers-are-for) revert cleanly — delete a layer and its values fall away. **A security change does not.**

A key's SD is a direct property of the key object. It is *not* tagged with a layer and it is *not* a write in the per-value contest. So when you change a key's DACL — tightening access, say — you are mutating the key itself, permanently. If a role layer existed at the time and is later uninstalled, the values it set revert, but the security change you made stays exactly where it is.

The reasoning is deliberate: security is **operational state, not configuration overlay.** Imagine the alternative — an administrator locks down a sensitive key while some unrelated role happens to be installed, and then removing that role silently reopens the key. Configuration is the kind of thing you want to revert in bundles; an access decision is not. So the registry keeps them on different tracks: values and key existence are layered and revertible; ownership and permissions are mutations on the object that outlive any layer.

The short version: **layers revert what the system is configured to do; they never revert who is allowed to do it.**

## Where to start

If you want to see how a process *reacts* to a change instead of polling for it — and how watch events report effective-state changes with the layering invisible — read [Watching for changes](~peios/registry/watches).

If you want the kernel/store split underneath all of this — who actually holds the SDs, and the trust boundary that follows — read [LCS and sources](~peios/registry/lcs-and-sources).

For the broader access model these rights plug into — the AccessCheck pipeline itself — read [Access decisions](~peios/access-decisions/overview).
