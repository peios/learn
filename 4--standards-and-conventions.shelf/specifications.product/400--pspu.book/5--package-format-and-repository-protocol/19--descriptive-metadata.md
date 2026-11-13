---
title: Descriptive Metadata
description: The fields that describe a package, its one-line description, its homepage, its license and the kind of terms that license is.
---

A package MAY carry descriptive fields. None affects how it resolves or
composes; each is covered by the package's identity.

| Field | Holds |
|---|---|
| `description` | A one-line description, in printable ASCII |
| `homepage` | The upstream project's `http` or `https` URL |
| `license` | The package's license, conventionally an SPDX expression |
| `license_class` | Which kind of terms the license is (below) |
| `source_license` | The license of the source it was built from, where it isn't the package's own |

None MAY be empty: an absent field is how a manifest says there is nothing.
`license` and `source_license` MUST NOT hold control characters. A
`homepage` MUST name a host.

## License classes

| Class | Meaning |
|---|---|
| `free` | Free software or open-source terms |
| `firmware` | Terms for device firmware, redistributable but not modifiable |
| `proprietary` | Other terms |
| `unknown` | Not recorded |

`unknown` is the default, and is recorded by leaving `license_class` out:
saying nothing and saying `unknown` mean the same.
