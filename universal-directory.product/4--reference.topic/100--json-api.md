---
title: The JSON API
type: reference
description: "Endpoint-by-endpoint reference for udd's JSON API: object CRUD, rename/move, attribute writes with per-value metadata, path resolution, the schema summary, and every error code."
related:
  - universal-directory/getting-started/running-udd
  - universal-directory/concepts/objects-and-identity
  - universal-directory/concepts/modifying-the-schema
---

Everything [`udd`](~universal-directory/getting-started/running-udd) can do is exposed as JSON under `/api`. The [debug console](~universal-directory/the-console/the-debug-console) is a client of this API and nothing more.

Requests and responses are `application/json`. **There is no authentication**: anyone who can reach the port has full control of the directory.

## Object payload

Endpoints that return an object use one shape:

```json
{
  "id": "9f2c…",                 // GUID (identity)
  "parent": "a01b…",             // GUID or null (root only)
  "name": "Jack",
  "class": "user",
  "classId": "c3d4…",
  "system": false,
  "facets": ["described", "person", "securityPrincipal"],   // effective surface
  "dn": "CN=Jack,OU=Sales",      // derived
  "path": "/Sales/Jack",         // derived
  "hasChildren": false,
  "stage": "alive",              // stored lifecycle stage (alive/deleted/shredded)
  "effectiveStage": "alive",     // stage after apply-time aging
  "ghost": false,                // class definition not yet in this node's schema
  "existence": { …stamp… },      // the existence atom's stamp (creation + stage transitions)
  "placement": { …stamp… },      // the (parent, name) atom's stamp
  "usnChanged": 51,              // node-private change-scan index
  "referencedBy": [              // the back-reference index: who points here
    { "id": "77aa…", "path": "/Admins", "attribute": "member" }
  ],
  "attributes": [
    { "name": "member",
      "values": [
        { "value": "b7e1…",
          "meta": { "expiry": ["2027-01-01T00:00:00Z"] },   // only when present
          "refPath": "/Sales/Jack",                         // reference syntax only; null unless target alive
          "refState": "alive",                              // alive / deleted / shredded / missing
          "stamp": { …stamp… } }                            // this value atom's stamp
      ],
      "absent": [                                           // only when present
        { "key": "c9a2…", "stamp": { …stamp… } }            // stamped residue of a removed value
      ] }
  ]
}
```

`refPath` appears only on values of reference-syntax attributes: the target's current native path, or `null` if the reference dangles.

Every merge atom — existence, placement, each attribute value — carries a **stamp**, the [replication record](~universal-directory/concepts/objects-and-identity) that decides merges:

```json
{
  "version": 2,                          // bumped per originating write to this atom
  "at": "2026-08-14T04:01:12Z",          // originating wall-clock time
  "origin": "e8a2…",                     // originating invocation id
  "cert": { "invocation": "e8a2…", "usn": 51 },   // transfer certificate (enumeration coordinate)
  "localUsn": 51                         // node-private
}
```

`absent` lists **absence atoms**: values (or, for a single-valued attribute, the whole attribute — `key: null`) that were removed and persist as stamped residue so the removal can win future merges. Rewriting an attribute with an unchanged value does not restamp it; multi-valued value sets are unordered and render in canonical (set-key) order.

Objects under a **derived repair** additionally carry `conflicted` / `orphaned` / `cycleBroken` flags, plus `effectiveName` (the CNF display name) and `effectiveParent` where they differ from the stored facts; `dn` and `path` always render the effective view. Child summaries carry `name` (effective), `ghost`, and the three repair flags.

## Endpoints

| Method & path | Purpose |
|---|---|
| `GET /api/node` | This node's replication identity and sync state: `{nodeId, invocationId, usn, hasRoot, purgeHorizon, morgueSize, rollbackLatched, erasureDebt, storage, boot, machine, utd, watermarks}` — `storage` carries the [durability marks](~universal-directory/concepts/persistence) (generation, durable vs appended bytes and USNs, dead flag), `boot` the boot report, `machine` this machine's identity (`{object, machineKey}` — the machine object's GUID and public key). |
| `GET /api/journal` | The node's observability journal (newest last, capped, survives restarts): `{at, kind, detail}` — merges that discarded concurrent input, refused records and pulls, derived repairs, rollback events. |
| `GET /api/storage` | The [storage view](~universal-directory/concepts/persistence): generation files with sizes, durability marks, rotation threshold, erasure debt, background-rebuild status and last outcome. |
| `GET /api/fabric` | The fabric view: this machine's identity and GIP bind, every discovered peer with its link state (`idle`/`dialing`/`connected`/`viaInbound`/`backoff`), live QUIC stats (RTT, congestion window, lost packets, MTU, wire bytes), inbound connections (each carrying `machine {guid, name}` once identified via `gip/ident`, null while unverified), **`channels`** (live channels: connection, peer, service, direction, age, bytes) and **`recentChannels`** (a ring of finished channels and failed opens with duration, bytes, and outcome), the supervisor's config, and a ring of timestamped fabric events. |
| `POST /api/fabric/redial/{guid}` | Debug: clear a peer's backoff and dial it now. |
| `GET /api/msgs` | The machine-talk log, oldest first (RAM only — capped at 200 records, gone on restart): each record is `{atMs, direction (in/out), peerGuid, peerName, text, outcome}`, where sent records carry `outcome` `delivered` (+`rttMs`), `failed` (+`detail`), or `unconfirmed` (+`detail`), and received records carry `received`. `{enabled: false}` on a node without a fabric. |
| `POST /api/msgs/send` | Send one `ud/msgs` message and block for its outcome (bounded: 5 s channel-open + 10 s ack). Body: `{"to", "text"}` — `to` is a machine GUID or a caseless machine name resolved against the fabric's targets; `text` is 1–16384 bytes. HTTP errors are for request problems only (`422 unknown-recipient`, `422 bad-text`, `503 no-fabric`); a send that ran returns `200` carrying the finished record, **including** `failed` and `unconfirmed` outcomes — those are data, not transport errors. |
| `POST /api/storage/rotate` | Debug: seal the active WAL, open the next generation, kick a background rebuild. |
| `POST /api/storage/rebuild` | Debug: kick a background snapshot rebuild (no rotation). |
| `GET /api/root` | The root object. |
| `GET /api/morgue` | Every tombstone: `{id, name, class, stage, effectiveStage, at, lastPath}`. |
| `POST /api/gc` | Run local GC now (harden aged tombstones, purge expired ones); returns the new horizon. |
| `POST /api/objects/{id}/restore` | Restore a soft-deleted object (top-down; refuses conflicts and elapsed windows). |
| `POST /api/objects/{id}/shred` | Security-erase (subtree-wide from alive, or escalate an existing soft delete). |
| `GET /api/objects/{id}` | One object by GUID. |
| `GET /api/objects/{id}/children` | Child summaries, in caseless name order: `{id, name, class, system, hasChildren}`. |
| `POST /api/objects/{id}/children` | Create a child. Body: `{"name", "class", "attributes"?}` — `attributes` maps attribute name → value list and is applied atomically with the create ([definitions are born whole](~universal-directory/concepts/modifying-the-schema)). Returns `201` + the object. |
| `PATCH /api/objects/{id}` | Rename and/or move (ModifyDN shape). Body: `{"name"?, "parent"?}`, `parent` by GUID. |
| `PUT /api/objects/{id}/attributes/{name}` | Replace an attribute's values wholesale. Body: `{"values": [{"value", "meta"?}]}`. An empty `values` deletes the attribute. Returns the updated object. |
| `DELETE /api/objects/{id}` | Soft-delete the object and its whole subtree (restorable tombstones). Returns `204`. |
| `GET /api/path` and `GET /api/path/{path}` | Resolve a native untyped path (caseless) to its object: `/api/path/Sales/Jack`. Bare `/api/path` is the root. |
| `GET /api/schema` | The compiled schema summary (below). |

Attribute names in URLs and bodies are caseless and accept wire names (`Acme-badgeColor`); the stored spelling is always the schema's canonical one.

Every mutating endpoint acknowledges only after the write is [durable](~universal-directory/concepts/persistence) — a `200`/`201`/`204` means the disk holds it. Attribute values are capped at 1 MiB each (large blobs are a future side-store's job, not an atom's).

## The schema summary

`GET /api/schema` returns the compiled schema, sorted by name:

```json
{
  "attributes": [ { "id", "name", "syntax", "singleValued", "matching", "aliases", "legalMeta" } ],
  "facets":     [ { "id", "name", "attributes": [ { "name", "required" } ] } ],
  "classes":    [ { "id", "name", "dnPrefix", "instantiable", "facets" } ],
  "extensions": [ { "id", "name", "targetClass", "facets" } ],
  "quarantined": [ { "id", "name", "reason" } ]
}
```

`quarantined` lists definitions excluded from the effective schema — replication can deliver a facet before its attributes. Compilation is *total*: it never fails, it quarantines what cannot join yet (with the reason) and lets it join automatically when its dependencies arrive. References to *tombstoned* definitions compile out instead (the facet keeps working minus its dead member). Originating schema writes are still strictly gated: a local write that would grow the quarantine is refused with `schema-violation`.

## Errors

Failures return `{"error": "<code>", "message": "<human text>"}` with:

| Code | Status | Meaning |
|---|---|---|
| `bad-object-id` | 400 | Path segment is not a GUID. |
| `no-such-object` | 404 | Object (or path/reference target) does not exist. |
| `no-root` | 503 | A joined store that has not yet received its first sync has no root. |
| `name-in-use` | 409 | Sibling name taken (caseless, type-blind). |
| `invalid-name` | 422 | Name fails [validity rules](~universal-directory/reference/naming-rules) (or definition-name grammar). |
| `unknown-class` | 422 | No class by that name. |
| `class-not-instantiable` | 422 | Class is marked non-instantiable (`domainRoot`, `configuration`). |
| `unknown-attribute` | 422 | No attribute definition by that name. |
| `attribute-not-permitted` | 422 | Attribute is outside the object's surface. |
| `single-valued` | 422 | Multiple values for a single-valued attribute (or meta). |
| `syntax-violation` | 422 | Value fails its syntax (bad integer/boolean/timestamp, non-GUID or dangling reference). |
| `illegal-meta-key` | 422 | Meta key unknown or not in the attribute's `legalMeta`. |
| `duplicate-value` | 409 | Value set contains duplicates under the matching rule. |
| `unknown-facet` | 422 | `attachedFacets` value is not a facet definition. |
| `facet-has-values` | 409 | Facet detach / extension delete refused while exclusively-provided attributes hold values. |
| `already-deleted` | 409 | Mutation aimed at a tombstone (restore first, or leave the dead be). |
| `ghost-object` | 409 | The object's class isn't in this node's schema yet; originating writes refuse until sync converges. |
| `rollback-quarantine` | 409 | The node detected it is running rolled-back (restored) state: its invocation was re-minted and originating writes are suspended until a completed pull heals it. |
| `not-restorable` | 409 | Restore refused: wrong stage, elapsed window, or parent not alive. |
| `root-is-protected` | 409 | The root cannot be deleted, renamed, or moved. |
| `system-object-protected` | 409 | System objects refuse moves and deletion (their attributes are writable). |
| `invalid-schema-placement` | 422 | Wrong class/parent combination in or around the schema subtree. |
| `schema-definition-immutable` | 409 | Definitions are add/delete only. |
| `definition-in-use` | 409 | [Unused-delete rule](~universal-directory/concepts/modifying-the-schema) refused the deletion; the message enumerates the blockers by name. |
| `schema-violation` | 422 | Trial recompile failed; the write was rolled back (message carries the compiler's reason). |
| `would-create-cycle` | 409 | Move would place an object under itself or a descendant. |
