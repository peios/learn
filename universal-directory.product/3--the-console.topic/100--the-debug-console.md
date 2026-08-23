---
title: The debug console
type: how-to
description: A tour of the udd debug console — the tree, the context menu, the surface-driven attribute table, and the morgue, schema, storage, fabric, msgs, and journal views.
related:
  - universal-directory/getting-started/running-udd
  - universal-directory/concepts/the-schema-model
  - universal-directory/concepts/modifying-the-schema
  - universal-directory/reference/json-api
---

The **debug console** is the browser UI served at [`udd`](~universal-directory/getting-started/running-udd)'s root URL.

It is deliberately a *debug* console. It shows everything the engine knows — GUIDs, system flags, unset attributes, per-value metadata, dangling references, replication stamps, durability marks — and every mutation the engine supports is reachable from it. Nothing in UD is console-only: the console is a client of the same [JSON API](~universal-directory/reference/json-api) you can drive with `curl`.

The header shows the node's **replication identity** — node id, invocation id, current local USN — and its **durability state**: the durable USN beside the RAM one, with a `⚠` marking a RAM-ahead moment, the active generation, and the WAL's size. Alarms surface here too, in red: a dead WAL, rollback quarantine, an overdue erasure debt. Hovering carries the full GUIDs and the boot report.

## The tree

The left pane is the directory tree, loaded lazily. Expand a node with its `▸` toggle, click a row to select it. Each row shows the object's *effective* name and a badge with its class. The schema is right there in the tree — browse `/Configuration/Schema` like any other subtree.

Objects under a **derived repair** carry a `⚠` marker; hover for which repair it is — a CNF display name, an orphan relocated into `/LostAndFound`, a broken move cycle. **Ghosts**, objects whose class definition has not reached this node, get a dashed `ghost` badge. The details pane spells the repair out beside the stored facts: `name conflict — displays as "sales CNF:…" (stored: sales)`.

**Moving objects is drag-and-drop**: drag a row onto the object that should become its new parent. The console deliberately does not second-guess the server. An illegal move — a cycle, a name conflict at the destination, a protected object — is refused by the engine and surfaces in the error banner at the top.

## The context menu

Right-clicking a tree row opens the object's operations menu.

**create child…** opens a modal with a name field, a class dropdown, and *a generated field for every attribute the chosen class's surface allows*. Multi-valued attributes get one-value-per-line textareas. Reference attributes accept a native path (`/Configuration/Schema/user`) or a raw GUID. When creating a facet definition, appending ` *` to a line of `attributes` marks that reference required. This is also how [schema definitions are authored](~universal-directory/concepts/modifying-the-schema), since definitions must be created complete.

**rename…** renames in place; identity and references are untouched.

**facets…** shows checkboxes for every facet. The class's own facets and extension-grafted facets are shown locked, marked `(class)` and `(extension)`; the rest toggle instance attachment. Detaching a facet whose attributes still hold values is refused by the engine.

**delete** soft-deletes the object *and its whole subtree* into the morgue, with confirmation.

**shred** is security erasure of the subtree, with a much scarier confirmation: payload destroyed, references scrubbed, no way back.

System objects offer only *create child*, and the engine refuses even that inside the schema subtree except for namespaces and definitions.

## The details pane

Selecting an object shows its identity card: GUID, class with a `(system)` marker where applicable, effective facets, DN, path, parent, plus the **existence and placement stamps** and the node-private `usnChanged` index.

Below it is the **attribute table**, which renders the object's *entire surface*, not just what is set:

- Attributes are **grouped by the facet** that provides them, in surface order; required attributes carry `*`.
- Unset attributes show as `(unset)` — the surface is the form.
- Each attribute has an inline `✎` editor: one value per line, empty saves as deletion. Metadata on values you do not touch is preserved.
- **Reference values render as `◈ /resolved/path`** with the raw GUID on hover. A reference whose target no longer exists shows in red as `◈ (dangling …)`.
- Per-value **metadata renders as chips** beside the value, such as `expiry = 2027-06-01T00:00:00Z`.
- Every value carries its **atom stamp** in dim text — `v2 · time · origin…`, with the transfer certificate and local USN on hover. Removed values linger as struck-through **absence atoms** stamped with their removal: replication residue, honestly shown.
- Engine-level data (`attachedFacets`) appears under an `(engine)` group, read-only, managed through the facets modal. Anything set outside the current surface still renders under `(outside surface)`, because stored data is never hidden.
- A **referenced by** section lists every holder pointing at this object, from the back-reference index, clickable.

Inspecting a tombstone via the morgue shows a **stage pill** — stored and effective stage — with an inline *restore* button while the window is open.

## The morgue

The **morgue** tab lists every tombstone the node holds: name (or a GUID stub for shredded skeletons), class, stage, the transition time, and the last known path. Stage shows `deleted → shredded` when apply-time aging has outrun physical GC.

Fleshy soft-deletes offer **restore** and **shred**; everything offers **inspect**. The header's **gc** button runs local garbage collection on demand, hardening tombstones past the restore window and purging those past `maxTimeApart`. The node-identity tooltip carries the current purge horizon.

## The schema view

The **schema** tab switches from the tree to a dedicated schema-management page — a faster surface over the same API for [authoring and tearing down definitions](~universal-directory/concepts/modifying-the-schema) during testing:

- Kind-grouped tables of every definition — namespaces with definition counts, attributes, facets, classes, extensions — with base definitions marked `(base)` and locked.
- **Purpose-built creation forms** per kind: selects for namespace, syntax, cardinality, and matching; checkbox pickers for `legalMeta`, facet attribute lists with a per-item *required* toggle, class facet composition, and extension targets. No GUIDs or paths to type.
- **Delete buttons** on user definitions, riding the engine's unused-delete rules. A refused deletion surfaces its reason, with the blockers named, in the error banner.
- A **quarantined** table whenever definitions are excluded from the effective schema because their dependencies have not replicated in yet, each with its reason.

Everything the schema view does can still be done manually through the tree. Definitions remain ordinary objects under `/Configuration/Schema`.

## The storage view

The **storage** tab is the [persistence layer's](~universal-directory/concepts/persistence) honest guts: how the store was booted (recovered from which snapshot, how many frames replayed, torn bytes truncated), the durable-versus-appended byte and USN marks, the **generation files table** with every snapshot and WAL, its size, and the active one marked, the outstanding **erasure debt** with its deadline, and the background rebuild's status and last outcome.

Two debug buttons drive compaction by hand: **rotate now** seals the active WAL, opens the next generation, and kicks a rebuild; **rebuild snapshot** kicks a rebuild alone. In normal life compaction runs itself, on size and on erasure obligations.

## The fabric view

The **fabric** tab is the GIP fabric drawn as a picture, live, auto-refreshing while visible.

At the top is **this machine's** identity strip: object GUID, key fingerprint, UDP bind, uptime, and a peers-connected badge.

Below it, **one card per peer machine**, each showing the *link itself*: a wire between "you" and the peer that flows with animation while the connection is up, its direction labelled **our dial** or **their dial** — the one-connection tiebreak's outcome made visible. Each card also carries the state badge (`connected` green, `via inbound` teal, `dialing` amber, `backoff` red with a live retry countdown and the last error), the address in use, RTT with a **sparkline** of recent samples, wire bytes both ways, MTU, congestion window, connection uptime, and a **redial** button. **Live channels** riding the connection appear as chips on the card, showing service name, direction, age, and bytes. Inbound connections that no channel has authenticated on yet appear as dashed **ghost cards** marked *unverified*.

Below the mesh sit two live logs. **Recent channels** lists every channel that ran — including `gip/ident`'s split-second conversations and failed opens — with service, direction, peer, duration, bytes, and a coloured outcome. The **fabric event stream** narrates every discovery, dial, ident, tiebreak (`superseded`, `adopted-inbound`), loss, and retry. The header's `fabric n/m` counter warns with ⚠ whenever a desired peer is down.

## The msgs view

The **msgs** tab is machine-to-machine talk over the fabric — the first real GIP service, `ud/msgs`, and deliberately *talk, not email*: online-only, no queueing, no storage, just a RAM ring of the last 200 records, gone on restart.

The compose bar holds a **peer dropdown** built from the fabric's targets, showing name and live link state, a text field, and **send**, which blocks until the message's fate is known. Below it is the chat log: received rows on the left, sent rows on the right, each sent row carrying its **outcome badge** — `delivered` green with the round-trip time, `unconfirmed` amber, `failed` red — with the honest detail on hover.

The three outcomes are the recipient-ACK protocol told straight. *Delivered* means the peer recorded the message before acking. *Failed* means provably not delivered. *Unconfirmed* is the Two-Generals residue: sent, then the channel died or timed out before the ack, reported as exactly that and never rounded to either certainty.

Every message is one short-lived channel, so sends also flash through the fabric tab's channel chips and recent-channels log.

## The journal

The **journal** tab lists the node's [replication](~universal-directory/concepts/replication) observability ring, because multi-master honesty means lost updates are never silent. It records every merge that **discarded** concurrent input, every **refused** record or pull (class mismatches, cross-domain attempts, over-horizon watermarks), every **repair** the derived view produced while merging, and every **rollback** detection event. Kinds are colour-coded; the newest entries are last.

## Errors and refresh

Engine refusals appear in the red banner with the API's error code and message — `name-in-use: an object with that name already exists here`. The console never pre-filters what the server would allow.

The **refresh** button reloads the tree, re-expands to your selection, and refetches the schema, picking up definitions created since the page loaded.
