---
title: release.toml
type: reference
description: The data file an edition ships at /usr/share/peios/release.toml — what it may contain, who reads it, and why it is data rather than something the package manager acts on.
related:
  - peios/peiso/editions-and-upgrades/editions
  - peios/peiso/editions-and-upgrades/upgrading-peios
  - peios/peiso/reference/the-spec
---

An edition package ships `/usr/share/peios/release.toml`. It states what the release asks of a system beyond its packages. peipkg never reads it; two tools do:

- **peiso**, when composing an image, to stage the seeds into the medium.
- **`upgrade-peios`**, after moving an installed system to a new release, to stage and apply the new release's seeds.

Both act as the operator, deliberately; the package manager acts as neither.

## Contents

```toml
# Peios 2026.8 Experimental. Read by peiso and upgrade-peios.
[registry]
autoapply = [
  "port-reservations",
  "eudev-service",
  "authd-service",
  "authd-policy",
  "lpsd-service",
  "lpsd-authd-registration",
  "lpsd-first-account",
  "login-console",
  "eventd-config",
  "eventd-service",
  "netd-service",
  "netd-default-profile",
  "resolvd-service",
  "resolvd-port",
  "atriumd-service",
]
```

### `[registry] autoapply`

Seed names, in the order they should apply. Each names a master a package in the edition's closure ships at `/usr/share/regim/<name>.reg`; listing it here is what opts it in. A reader treats a name nothing ships as an error.

Nothing else is defined yet. Unknown keys are rejected by both readers, so the file can grow without silently meaning nothing to an older tool.

## What is not here

- **`dwed-service`.** The DWE seed is peiso's to add, for a development medium only; a release never applies it.
- **Anything a medium adds.** `live-boot` and the medium repository are the image's, not the release's.
- **Seeds that were removed between releases.** A seed present in 2026.8 and absent in 2026.9 is not un-applied by anything today; the registry keeps its history and that is where the record lives. This is the same limitation an edition has with packages it stops depending on, and it is deferred to the same future mechanism.

## Why a file, and not a package field

peipkg's manifest is the wrong place for this, on purpose. A field the package manager acted on — "apply these seeds when I am installed" — would let any package change system policy by being installed, which is the one thing Peios packages must not be able to do. As a file that only deliberate tools read, the list is inert until someone who has chosen to build an image or upgrade a system acts on it.
