---
title: "identity.*"
description: "Every field the evman catalogue defines under identity: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `identity`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="identity.sids"></a>`identity.sids`

- **Type:** `bin.sid[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

The user SIDs of the well-known identities the kernel mints at boot:
today SYSTEM (S-1-5-18) and Anonymous Logon (S-1-5-7), the roots of every
identity on the system. A boot record without one of them means that
token could not be built — a failure the code otherwise returns silently.

**Carried by:**

No event carries this field yet.

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
