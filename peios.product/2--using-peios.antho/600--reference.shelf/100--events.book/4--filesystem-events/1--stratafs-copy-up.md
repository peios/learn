---
title: STRATAFS_COPY_UP
description: The event fired on every StrataFS copy-up, successful or not — six keys, no caller identity, and where ENOTDIR actually surfaces.
---

Fires on every StrataFS copy-up, successful or not.

Event type string: `STRATAFS_COPY_UP`.

| Key | Meaning |
|---|---|
| `path` | The relative path within the mount, `/`-prefixed. |
| `provider_index` | The stratum the object was copied from. |
| `provider_stratum` | That stratum's path. |
| `create_index` | The stratum it was copied into. |
| `create_stratum` | That stratum's path. |
| `result_errno` | Zero on success, the failure otherwise. |

Six keys, and no seventh.

## No caller in the payload

Nothing here names a token, and that is not an omission.

Copy-up preserves the source object's descriptor, so the resulting file
records nothing about who caused it to exist. The caller is recovered
from the **envelope** instead: KMES stamps the effective, true and
process token GUIDs onto the header at ring-write time, and because
copy-up runs in the caller's own context, those are the caller's
(§1.2).

A consumer reading only payloads will conclude these events are
anonymous. They are not — the identity is one level out.

## ENOTDIR arrives here, not in the refusal event

A parent materialisation that fails with `ENOTDIR` is reported through
this event, carried in `result_errno`, rather than through
`STRATAFS_MUTATION_REFUSED` (§4.2).

That is worth knowing when searching for a refusal and finding nothing:
the record exists, under a different type, with all the required fields
present.
