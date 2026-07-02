---
title: rsi/source.h — Becoming a source
type: reference
description: Complete reference for <rsi/source.h> — registering as a Peios registry source and obtaining the source fd on which the RSI protocol is served.
related:
  - peios-sdk/registry-sources/overview
  - peios-sdk/reference/rsi-request
  - peios/the-registry/overview
---

`<rsi/source.h>` is where a registry **source** begins. A source is a storage backend for the [LCS registry](~peios-sdk/registry/overview) — the provider counterpart to libpeios's registry *client*. Where a client opens keys and reads values, a source is what actually *holds* those keys and values and answers the kernel's requests for them.

This header has one job: **registration**. You declare which hives your process backs, register with the kernel, and get back a **source fd**. From that point on you serve the RSI (Registry Source Interface) protocol on that fd — [reading requests](~peios-sdk/reference/rsi-request) and [writing responses](~peios-sdk/reference/rsi-response). Registration requires `SeTcbPrivilege`. The RSI wire constants (`RSI_HIVE_PRIVATE`, `RSI_*`) come from `<pkm/lcs.h>`.

This is part of **librsi**, a separate library from libpeios — link `-lrsi` and include `<rsi.h>` (or the individual `<rsi/*.h>`). It follows the same [library conventions](~peios-sdk/getting-started/library-conventions): raw fds, `int` returning `0`/`-1`+errno, and the errno passed straight through from the kernel.

## Describing a hive

A **hive** is a subtree of the registry with its own root key. A source declares one `struct rsi_hive` per hive it backs:

```c
struct rsi_hive {
    const void *name;         /* hive name (not NUL-terminated) */
    uint32_t    name_len;
    uint32_t    flags;        /* RSI_HIVE_PRIVATE, or 0 for a global hive */
    uint8_t     root_guid[16];/* root key GUID */
    uint8_t     scope_guid[16];/* private hives; zero for a global hive */
};
```

| Field | Meaning |
|---|---|
| `name` / `name_len` | The hive's name, length-counted (not NUL-terminated). |
| `flags` | `RSI_HIVE_PRIVATE` for a private (scoped) hive, or `0` for a global one. |
| `root_guid` | The GUID of the hive's root key — the anchor every path in the hive resolves from. |
| `scope_guid` | For a **private** hive, the scope GUID that bounds who can resolve it; **zero for a global hive**. |

A **global** hive is visible system-wide; a **private** hive is scoped by `scope_guid` and resolvable only by tokens holding that scope (see the token [LCS credentials](~peios-sdk/reference/token#lcs-registry-credentials)). Set `RSI_HIVE_PRIVATE` and a non-zero `scope_guid` together for a private hive; leave both clear for a global one.

## Registering

```c
int rsi_register(const struct rsi_hive *hives, uint32_t count, uint64_t max_sequence);
```

Opens `/dev/pkm_registry` and registers all `count` hives in one call, returning the **source fd** — the descriptor you then `read(2)` requests and `write(2)` responses on — or `-1` with `errno`.

| Argument | Meaning |
|---|---|
| `hives` / `count` | The hives this source serves. `count` must be `>= 1`; the kernel enforces its configured `MaxHivesPerSource` limit. |
| `max_sequence` | The highest sequence number this source has **already persisted**. The kernel resumes its global sequence counter *past* this value, so a source that has durable state from a previous run must report it here to avoid reusing sequence numbers. A fresh source with no persisted state passes `0`. |

Errors include `EPERM` (no `SeTcbPrivilege`), `EINVAL`, `ENOSPC` (over the hive limit), `ENOMEM`, `EFAULT`, and any error from the underlying `/dev/pkm_registry` `open(2)`.

```c
struct rsi_hive hive = {
    .name = "MyStore", .name_len = 7,
    .flags = 0,                                  /* global hive */
    .root_guid = { /* … 16 bytes … */ },
};

int src = rsi_register(&hive, 1, /*max_sequence=*/0);
if (src < 0) { perror("rsi_register"); return -1; }
/* `src` is now the source fd — serve the RSI protocol on it. */
```

The `max_sequence` parameter is the one piece of state a durable source must get right: on restart, scan your persisted data for the highest sequence you ever wrote and pass it, so the kernel never hands out a sequence number you've already used.

## What comes next

Registration is the whole of this header. Once you hold the source fd, the serve loop lives in the other two:

- **[`<rsi/request.h>`](~peios-sdk/reference/rsi-request)** — read and decode the requests the kernel sends.
- **[`<rsi/response.h>`](~peios-sdk/reference/rsi-response)** — build and send the replies.

The [serving requests](~peios-sdk/registry-sources/serving-requests) guide ties them together into a working serve loop.

## See also

- **[Registry sources overview](~peios-sdk/registry-sources/overview)** — what a source is and how the RSI protocol flows.
- **[The registry](~peios/the-registry/overview)** — the operator-side model of hives, layers, and sources.
