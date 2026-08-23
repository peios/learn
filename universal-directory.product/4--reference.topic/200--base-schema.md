---
title: The base schema
type: reference
description: "Every attribute, facet, and class in UD's base schema — the 48 system definitions materialised at domain creation — with syntaxes, matching rules, compositions, and DN prefixes."
related:
  - universal-directory/concepts/the-schema-model
  - universal-directory/concepts/modifying-the-schema
  - universal-directory/reference/naming-rules
---

The **base schema** is the set of system definitions every directory is born with: 26 attributes, 11 facets, and 11 classes — 48 objects in all, flat under `/Configuration/Schema` and immutable forever.

All new definitions live in [namespaces](~universal-directory/concepts/modifying-the-schema); the unprefixed name space tabulated below is reserved. The base definitions are minted at **domain creation** by the first node, as its ordinary originating writes. There are no well-known GUIDs — a joining node receives everything by sync.

## Attributes

| Attribute | Syntax | Values | Matching | Aliases | legalMeta |
|---|---|---|---|---|---|
| `description` | string | multi | caseless | | |
| `displayName` | string | single | caseless | | |
| `givenName` | string | single | caseless | | |
| `surname` | string | single | caseless | `sn` | |
| `email` | string | multi | caseless | `mail` | |
| `sid` | string | single | exact | `objectSid` | |
| `member` | reference | multi | exact | | `expiry` |
| `expiry` | timestamp | single | exact | | |
| `syntax` | string | single | caseless | | |
| `singleValued` | boolean | single | exact | | |
| `matching` | string | single | caseless | | |
| `legalMeta` | reference | multi | exact | | |
| `aliases` | string | multi | caseless | | |
| `lifecycle` | string | single | caseless | | |
| `system` | boolean | single | exact | | |
| `attributes` | reference | multi | exact | | `required` |
| `required` | boolean | single | exact | | |
| `facets` | reference | multi | exact | | |
| `attachedFacets` | reference | multi | exact | | |
| `dnPrefix` | string | single | caseless | | |
| `targetClass` | reference | single | exact | | |
| `instantiable` | boolean | single | exact | | |
| `maxTimeApart` | integer | single | exact | | |
| `timeUntilShred` | integer | single | exact | | |
| `networkAddress` | endpoint | multi | caseless | | |
| `machineKey` | publicKey | multi | exact | | |

Notes: `description` is multi-valued (following the LDAP RFCs where they and Active Directory disagree). `attachedFacets` is engine-level — legal on every object regardless of surface, and the vehicle for [instance facet attachment](~universal-directory/concepts/the-schema-model). Aliases are recorded on definitions but not yet used for lookup. `expiry` and `required` exist to serve as meta keys (on `member` and `attributes` respectively). `instantiable` (unset = true) marks classes users may instantiate. `maxTimeApart` and `timeUntilShred` are the domain's lifecycle knobs, in seconds, held on the `/Configuration` object itself: `timeUntilShred` is the restore window (default 30 days — past it a soft-deleted record hardens to a skeleton), `maxTimeApart` the purge horizon and future partition contract (default 180 days — past it tombstones purge entirely). `networkAddress` holds a machine's network endpoints — multi-valued because a DNS name, an IPv4, and an IPv6 address are legitimately concurrent addresses of one machine.

### The `endpoint` syntax

`networkAddress` uses the **`endpoint`** value syntax: `host[:port]`, where the host is a DNS name, an IPv4 literal, or a **bracketed** IPv6 literal (`[2001:db8::1]:6000`), and an omitted port designates the well-known **GIP port, 5390** (GIP — the General Interlink Protocol — is UD's intra-domain machine-to-machine protocol; the syntax ships today, the protocol does not yet). The grammar is deliberately strict, because a loose syntax can never be tightened once values persist:

- no schemes (`quic://…`) and no whitespace anywhere;
- DNS names are ASCII (IDN arrives as punycode), dot-separated labels of letters, digits, and interior hyphens, ≤ 63 bytes per label and ≤ 253 total, with no trailing dot;
- anything whose last label is all digits must be a *valid* IPv4 literal — `999.1.1.1` is refused rather than silently treated as a DNS name — and leading zeros in octets (historical octal) are refused;
- IPv6 must be bracketed, zone ids (`%eth0`) are refused;
- an explicit port is 1–65535 with no leading zeros.

Values compare caselessly as opaque strings: `DC1.corp` and `dc1.CORP` are the same set member, but `dc1.corp` and `dc1.corp:5390` are two distinct values even though they designate the same place — set matching is literal; interpreting endpoints is the dialer's job.

### The `publicKey` syntax

`machineKey` uses the **`publicKey`** value syntax: `<algorithm>:<hex>`, where the only algorithm today is `x25519` and the payload is exactly 64 **lowercase** hex characters (32 bytes) — one canonical spelling per key, compared exactly. This is the machine's GIP identity key: [`udd new`](~universal-directory/getting-started/running-udd) mints the keypair at enrollment, keeps the private half in the data directory's `machine-key` file, and records the public half here, replicated like any other fact. The attribute is multi-valued so a future key *rotation* can hold old and new keys through an overlap window. The algorithm prefix is deliberate agility: a future signing key gets a new prefix, not a new syntax.

## Facets

| Facet | Attributes (`*` = required) |
|---|---|
| `described` | `description`, `displayName` |
| `person` | `givenName`, `surname`, `email` |
| `securityPrincipal` | `sid` * |
| `membership` | `member` |
| `schemaDefinition` | `aliases`, `lifecycle` *, `system` * |
| `attributeSchema` | `syntax` *, `singleValued` *, `matching` *, `legalMeta` |
| `facetSchema` | `attributes` |
| `classSchema` | `facets`, `dnPrefix`, `instantiable` |
| `extensionSchema` | `targetClass` *, `facets` * |
| `replicationConfig` | `maxTimeApart`, `timeUntilShred` |
| `machine` | `networkAddress`, `machineKey` |

Required-ness is enforced today only where compilation demands it (schema definitions must be born complete); enforcement for ordinary objects is pending.

`machine` is the surface for anything reachable on the network; both attributes are deliberately optional on it — a pre-staged machine that has not yet enrolled has neither an address nor a key. The `computer` class composes it, and [`udd new`](~universal-directory/getting-started/running-udd) creates one `computer` object for the machine it runs on. (The class is not called `machine` because definitions are siblings under `/Configuration/Schema`, where names are unique regardless of kind — the facet holds that name.)

## Classes

| Class | dnPrefix | Instantiable | Facets |
|---|---|---|---|
| `domainRoot` | — (never in a DN) | no | `described` |
| `organizationalUnit` | `OU` | yes | `described` |
| `user` | `CN` | yes | `described`, `person`, `securityPrincipal` |
| `group` | `CN` | yes | `described`, `securityPrincipal`, `membership` |
| `attributeDefinition` | `CN` | yes | `described`, `schemaDefinition`, `attributeSchema` |
| `facetDefinition` | `CN` | yes | `described`, `schemaDefinition`, `facetSchema` |
| `classDefinition` | `CN` | yes | `described`, `schemaDefinition`, `classSchema` |
| `schemaNamespace` | `OU` | yes | `described` |
| `classExtension` | `CN` | yes | `described`, `schemaDefinition`, `extensionSchema` |
| `configuration` | `CN` | no | `described`, `replicationConfig` |
| `computer` | `CN` | yes | `described`, `machine` |

The self-hosting anchor: the `classDefinition` object under `/Configuration/Schema` is an instance of itself; every other definition's kind resolves from there.

An instantiable class must carry a `dnPrefix` (compile-enforced); non-instantiable classes are engine-created only. `/Configuration` is the singleton `configuration` instance — its class composition is what makes the replication knobs writable there, and future config areas graft on via `classExtension`. Besides `/Configuration/Schema`, the base tree also contains **`/LostAndFound`**, a system OU born with the domain: the destination [replication repairs](~universal-directory/concepts/replication) derive orphans and broken cycles into (the domain root is a replication head from birth). It also contains **`/Domain Controllers`**, the default home for machine objects — a convention, not structure: nothing in UD locates domain controllers by path, and a machine object is free to live anywhere.
