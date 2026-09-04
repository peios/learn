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
  "login-console",
  "eventd-config",
  "eventd-service",
  "netd-service",
  "netd-default-profile",
  "resolvd-service",
  "resolvd-port",
  "atriumd-service",
]

# The boot medium applies these and an installed machine does not.
live_autoapply = [
  "lpsd-first-account",
]

# Only an installed machine applies these.
install_autoapply = [
  "oobe-service",
]
```

## Three lists, because a seed has a place

A seed can belong to the medium, to the machine an installer writes, or to both. The distinction exists because **an installer copies the shipped image verbatim**: whatever is staged onto the medium arrives on the disk too, unless something takes it off again.

Two opposite cases make that matter, and before the split neither could be said:

- `lpsd-first-account` provisions the development account **whose password ships in the image and is therefore public**. Right on a live medium; a hole on an installed machine — which used to get it, and then crash the provisioner against its own account on every subsequent boot.
- `oobe-service` runs [first-boot setup](~peios/disks-and-filesystems/first-boot-setup), which asks for a real account. Right on an installed machine; on the medium it would take the console away from the installer.

| Key | Staged into | Applied by |
|---|---|---|
| `autoapply` | `lcl/policy/autoapply.d/` | every system, on first boot |
| `live_autoapply` | `lcl/policy/autoapply.live.d/` | the boot medium only |
| `install_autoapply` | `lcl/policy/autoapply.install.d/` | the installed machine only |

Each names a master a package in the edition's closure ships at `/usr/share/regim/<name>.reg`; listing it is what opts it in. A reader treats a name nothing ships as an error, and a name in two lists as an error too — it would be staged and drained twice, and in every case it means the release said something it did not mean.

peinit's drain applies the first two, base before live, so a live seed can override a value the base one set: the medium is the special case, and the special case goes last. It never touches the third. The installer is what promotes `autoapply.install.d/` into the target's `autoapply.d/` and deletes `autoapply.live.d/` — the act that turns a copy of a medium into a system.

Nothing else is defined yet. Unknown keys are rejected by both readers, so the file can grow without silently meaning nothing to an older tool.

## What is not here

- **`dwed-service`.** The DWE seed is peiso's to add, for a development medium only; a release never applies it. peiso stages it into the **live** queue, on the same reasoning that puts the development account there: a machine installed from a DWE medium is a machine, and a vsock control channel into it is not something the operator asked for.
- **Anything a medium adds.** `live-boot` and the medium repository are the image's, not the release's.
- **Seeds that were removed between releases.** A seed present in 2026.8 and absent in 2026.9 is not un-applied by anything today; the registry keeps its history and that is where the record lives. This is the same limitation an edition has with packages it stops depending on, and it is deferred to the same future mechanism.

## Why a file, and not a package field

peipkg's manifest is the wrong place for this, on purpose. A field the package manager acted on — "apply these seeds when I am installed" — would let any package change system policy by being installed, which is the one thing Peios packages must not be able to do. As a file that only deliberate tools read, the list is inert until someone who has chosen to build an image or upgrade a system acts on it.
