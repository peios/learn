---
title: Manifest
---

The manifest is the authoritative metadata for a package. It
declares the package's identity, dependencies, side-effect
requirements, and build provenance.

The manifest is a JSON document stored at
`.peipkg/manifest.json` inside the package archive. It MUST
conform to RFC 8259 and to the schema defined in this
section.

## Top-level schema

```json
{
  "schema_version": 1,
  "name": "<string>",
  "version": "<string>",
  "architecture": "<string>",
  "description": "<string>",
  "license": "<string>",
  "homepage": "<string>",
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
| `schema_version` | integer | Manifest schema version. MUST be 1 in this specification. |
| `name` | string | Package name conforming to §2.1. |
| `version` | string | Package version conforming to §2.2. |
| `architecture` | string | Architecture identifier conforming to §2.3. |
| `dependencies` | array | List of required dependencies. MAY be empty. Element schema in §4.1.1. |
| `conflicts` | array | List of conflicting packages. MAY be empty. Element schema in §4.1.2. |
| `size_installed` | integer | Total size in bytes of installed payload. Required to enable consumer-side decompression bounds enforcement (§3.5.4). |
| `build` | object | Build provenance. Schema below. |

A manifest missing any required field MUST be rejected as
invalid.

## Optional fields

| Field | Type | Description | Default if absent |
|---|---|---|---|
| `description` | string | One-line human-readable description. | empty string |
| `license` | string | SPDX license identifier or expression. | empty string |
| `homepage` | string | URL of the upstream project. | empty string |
| `optional_dependencies` | array | Dependencies that enhance functionality but are not required. | empty array |
| `provides` | array | Virtual packages or capabilities this package provides. | empty array |
| `replaces` | array | Packages this one supersedes (rename succession). | empty array |
| `side_effects` | array | Standard maintenance operations to invoke on install. See §4.3. | empty array |
| `sd_overrides` | array | Per-payload-entry security descriptor overrides. See §3.3.5 and §3.4. | empty array |

A manifest containing an unknown field MUST NOT be rejected;
the unknown field MUST be ignored. This permits forward-
compatible extension.

## Build object

```json
{
  "timestamp": "<RFC 3339 timestamp>",
  "farm_id": "<string>",
  "source_ref": "<string>"
}
```

| Field | Type | Description |
|---|---|---|
| `timestamp` | string | ISO 8601 / RFC 3339 timestamp of build. MUST be UTC and end with `Z`. |
| `farm_id` | string | Identifier of the build farm that produced this package. |
| `source_ref` | string | Reference to the build inputs sufficient to reproduce the build. |

The `timestamp` is also the value used for every tar entry's
modification time (§3.1.4). Producers MUST set both
identically.

The `source_ref` form is producer-defined but SHOULD be a
machine-resolvable reference. The conventional form is a
git URL with explicit ref:

```
git+https://git.peios.org/sources/nginx#refs/tags/v1.26.2-3
```

> [!INFORMATIVE]
> The build object enables reproducibility verification: a
> third party in possession of the build inputs and the
> recorded timestamp can re-run the build and check that the
> output bytes match. The format does not mandate this
> verification; it provides the inputs.

## SD override object

A single entry in `sd_overrides` has the form:

```json
{
  "path": "<payload-relative path>",
  "sd": "<base64-encoded SD>"
}
```

| Field | Type | Description |
|---|---|---|
| `path` | string | Payload-relative path of a file or directory entry. MUST exactly match the path of a corresponding tar entry. |
| `sd` | string | Base64-encoded binary self-relative security descriptor (PSD-004 §3.12), encoded per RFC 4648 §4 without padding. |

The `path` value MUST refer to a regular-file entry or a
directory entry in the tar archive. SD overrides MUST NOT
target symlink entries.

An override referring to a non-existent payload entry, or
to a symlink entry, is INVALID and MUST cause the package to
be rejected.

The `sd` value MUST decode to a syntactically valid binary
self-relative SD per PSD-004 §3.12. An override whose
decoded SD bytes do not parse is INVALID and MUST cause the
package to be rejected.

The `sd_overrides` array MUST be sorted lexicographically by
`path`.

> [!INFORMATIVE]
> The default behavior — when a payload entry has no SD
> override — is for the file or directory to be created with
> no caller-supplied SD, causing the kernel to compute an
> inherited SD from the parent directory at creation time
> (PSD-004 §3.6). Most packages declare no overrides at all.
> Overrides are reserved for entries where inherited SDs are
> inappropriate. See §3.4 for the application procedure.

## Field constraints

The `description` field, when present, SHOULD be a single
line under 80 characters. Longer descriptions belong in
upstream documentation, not the manifest.

The `license` field, when present, SHOULD be a valid SPDX
license expression. The producer MAY use other forms; the
specification does not validate license strings.

The `homepage` field, when present, MUST be a syntactically
valid URL per RFC 3986.

The `size_installed` field MUST be a non-negative integer
expressing bytes. It is the total size of the installed
payload (the sum of all regular-file `size` fields in
`files.json`), used by consumers for disk-space planning
(§7.1.2.2) and decompression-bound enforcement (§3.5.4).

The `description` field MUST consist only of printable
ASCII characters in the range `0x20`-`0x7E`. ASCII control
characters and non-ASCII bytes MUST NOT appear in the
`description`. This prevents terminal escape-sequence
injection when the description is shown to operators.

The `homepage` field, when present, MUST use the `https`
or `http` URL scheme. Other schemes (`javascript:`,
`file:`, `data:`, etc.) MUST cause the package to be
rejected.

## Authoritative status

The manifest is authoritative for the package's metadata. If
the manifest disagrees with any other source (the repository
index, the package filename, secondary documentation), the
manifest MUST be treated as correct.

> [!INFORMATIVE]
> The repository index (§6.2) extracts a subset of manifest
> fields for client-side resolution. The index is a derived
> view; the manifest is the source. Any tooling that
> generates an index MUST extract values directly from
> package manifests.

## Encoding

The manifest MUST be UTF-8 encoded JSON. The file MUST end
with a single newline character.

The manifest MAY be pretty-printed (with whitespace and
indentation) or compact. Whitespace differences do not
affect semantics. For reproducibility, a producer SHOULD
choose one canonical form and use it consistently.

> [!INFORMATIVE]
> A canonical form is recommended for reproducibility because
> the manifest's bytes are part of the tar archive that gets
> hashed and signed. Two manifests with semantically
> equivalent JSON but different whitespace produce different
> archives.
