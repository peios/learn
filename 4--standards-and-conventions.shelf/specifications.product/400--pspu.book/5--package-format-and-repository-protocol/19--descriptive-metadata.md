---
title: Descriptive Metadata
description: The fields that describe a package, its one-line description, its homepage, its license, the kind of terms that license is, and the package holding its corresponding source.
---

A package MAY carry descriptive fields. None affects how it resolves or
composes; each is covered by the package's identity.

| Field | Holds |
|---|---|
| `description` | A one-line description, in printable ASCII |
| `homepage` | The upstream project's `http` or `https` URL |
| `license` | The package's license, conventionally an SPDX expression |
| `license_class` | Which kind of terms the license is (below) |
| `source` | The package holding the corresponding source it was built from (below) |
| `source_license` | The license of the source it was built from, where it isn't the package's own |

None MAY be empty: an absent field is how a manifest says there is nothing.
`license` and `source_license` MUST NOT hold control characters. A
`homepage` MUST name a host.

## Corresponding source

`source` is a package ID in its string form (§5.2), with its `?arch=`
part, naming the package
that holds the complete source the package was built from: the upstream
source, the patches applied to it, and the files that controlled the
build. It SHOULD name a `noarch` package, since source is the same for
every architecture, such as `org.gnu.bash-source@5.3.20-1?arch=noarch`.

A source package holds its source under `/usr/src/dist/` (§5.14). Several
packages built from one source name the same source package. A package
whose upstream artifact is itself what ships, such as device firmware,
has no source to name and leaves `source` out.

A repository that publishes a package naming a source SHOULD publish that
source package beside it, so that the source can be found from the
package alone.

## License classes

| Class | Meaning |
|---|---|
| `free` | Free software or open-source terms |
| `firmware` | Terms for device firmware, redistributable but not modifiable |
| `proprietary` | Other terms |
| `unknown` | Not recorded |

`unknown` is the default, and is recorded by leaving `license_class` out:
saying nothing and saying `unknown` mean the same.
