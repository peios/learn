---
title: The Manifest
description: The authoritative JSON metadata for a package — identity, relationships, side-effect requirements and build provenance — with its full schema.
---

The manifest is the authoritative metadata for a package: its identity,
its relationships, its side-effect requirements, and its build
provenance. It is a JSON document at `.peipkg/manifest.json`.

## Schema

```json
{
  "schema_version": 1,
  "name": "<string>",
  "version": "<string>",
  "architecture": "<string>",
  "description": "<string>",
  "license": "<string>",
  "homepage": "<string>",
  "default_root": "<root reference>",
  "special_system_package": <bool>,
  "dependencies": [<dependency>...],
  "optional_dependencies": [<dependency>...],
  "conflicts": [<dependency>...],
  "provides": [<provides>...],
  "replaces": [<replaces>...],
  "side_effects": [<string>...],
  "size_installed": <integer>,
  "sd_overrides": [<sd_override>...],
  "build": {<build>}
}
```

## Required fields

| Field | Type | Description |
|---|---|---|
| `schema_version` | integer | MUST be 1 in this version. |
| `name` | string | Package name conforming to §5.3. |
| `version` | string | Version conforming to §5.5. |
| `architecture` | string | Architecture identifier conforming to §5.8. |
| `dependencies` | array | Required dependencies. MAY be empty; MUST be present. |
| `conflicts` | array | Conflicting packages. MAY be empty; MUST be present. |
| `size_installed` | integer | Total size in bytes of the installed payload. |
| `build` | object | Build provenance. |

A manifest missing any required field MUST be rejected.

## Optional fields

| Field | Type | Description | Absent means |
|---|---|---|---|
| `description` | string | One-line human-readable description. | empty string |
| `license` | string | SPDX identifier or expression. | empty string |
| `homepage` | string | URL of the upstream project. | empty string |
| `default_root` | string | The root a *top-level* install of this package lands in when the operator names none (§5.19). | the operator's current root |
| `special_system_package` | boolean | Declares the package exempt from the §5.14 layout rules at production time (§5.14). | `false` |
| `optional_dependencies` | array | Dependencies that enhance but are not required. | empty array |
| `provides` | array | Virtual names this package satisfies. | empty array |
| `replaces` | array | Packages this one supersedes. | empty array |
| `side_effects` | array | Maintenance operations to invoke (§5.24). | empty array |
| `sd_overrides` | array | Per-entry security descriptor overrides (§5.20). | empty array |

A manifest carrying an unknown field MUST NOT be rejected; the unknown
field MUST be ignored (§5.9).

## The build object

```json
{
  "timestamp": "<RFC 3339 timestamp>",
  "farm_id": "<string>",
  "source_ref": "<string>"
}
```

| Field | Required | Description |
|---|---|---|
| `timestamp` | yes | RFC 3339 timestamp of the build. MUST be UTC, MUST end with `Z`, and MUST NOT carry sub-second precision. |
| `farm_id` | yes | Identifier of the build farm that produced this package. |
| `source_ref` | yes | Reference to the build inputs, sufficient to reproduce the build. |
| `source_package` | no | Name of the corresponding-source package produced from the same recipe and inputs (§5.15). |
| `recipe_ref` | no | VCS identity of the recipe tree the build ran from — for example `git:<commit>`, suffixed `+dirty` when the work tree held uncommitted changes. |
| `builder` | no | Identity and revision of the producing tool, for example `pekit/<revision>`. |

A consumer MUST treat an absent optional field as the empty value.

`timestamp` is also the modification time of every tar entry (§5.11
rule 2). A producer MUST set both identically.

`source_ref` is producer-defined but SHOULD be a machine-resolvable
reference. The conventional form is a version-control URL with an
explicit ref:

```
git+https://git.peios.org/sources/nginx#refs/tags/v1.26.2-3
```

> [!NOTE]
> The build object exists to make reproducibility verifiable: a third
> party in possession of the build inputs and the recorded timestamp can
> re-run the build and compare the output bytes. The format does not
> mandate that verification; it supplies the inputs for it.

## Field constraints

`description`, when present, MUST consist only of printable ASCII in the
range `0x20`–`0x7E`. ASCII control characters and non-ASCII bytes MUST
NOT appear. It SHOULD be a single line under 80 characters; longer
descriptions belong in upstream documentation.

> [!NOTE]
> The byte-range rule is deliberately cruder than a Unicode-category
> test. `description` is displayed to an operator deciding whether to
> install, so it is both a terminal-escape-injection surface and a
> homoglyph surface. A hard ASCII whitelist closes both without anyone
> having to reason about which Unicode categories are safe to render.

`license`, when present, SHOULD be a valid SPDX expression. A producer
MAY use another form; this specification does not validate license
strings.

`homepage`, when present, MUST be a syntactically valid URL per RFC 3986
and MUST use the `https` or `http` scheme. Any other scheme MUST cause
the package to be rejected.

`size_installed` MUST be a non-negative integer, and MUST equal the sum
of the `size` fields of every entry in the files manifest (§5.25). A
consumer MUST verify that equality and MUST reject a package where it
does not hold.

> [!NOTE]
> `size_installed` is not merely advisory. It is the input to the
> decompression bound of §5.27, so a package whose declared size is
> smaller than what it actually unpacks to is a resource-exhaustion
> attempt, and one that is larger inflates the bound. Tying it to a
> quantity a consumer can independently compute is what makes it
> trustworthy.

## Authoritative status

The manifest is authoritative for a package's metadata. Where it
disagrees with any other source — the repository index, the filename,
secondary documentation — the manifest MUST be treated as correct, and
the disagreement MUST be reported (§5.32).

## Encoding

The manifest MUST be UTF-8 encoded JSON and MUST end with a single
newline.

A producer that intends its packages to be byte-reproducible MUST
serialise the manifest canonically: compact, with no insignificant
whitespace, with HTML-escaping of `<`, `>`, and `&` disabled, with
fields in the declaration order of the schema above, and with every
optional field either always emitted or never emitted for a given
producer.

> [!NOTE]
> The manifest's bytes are inside the archive that gets hashed and
> signed, so two semantically identical manifests with different
> whitespace produce different packages. Pinning the serialisation is
> what makes independent reproduction possible at all; leaving it to the
> producer's discretion means only that producer can ever reproduce its
> own output.
