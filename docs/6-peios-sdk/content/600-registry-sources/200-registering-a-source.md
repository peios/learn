---
title: Registering a source
type: how-to
description: Declare the hives your source backs and register with the kernel to obtain the source fd.
related:
  - peios-sdk/reference/rsi-source
  - peios-sdk/registry-sources/serving-requests
---

Every source starts by registering. You tell the kernel which hives your process backs, and it hands you a source fd to serve on. The full detail is in [`rsi/source.h`](~peios-sdk/reference/rsi-source); this guide walks the decisions.

## Declare your hives

A hive is a registry subtree with its own root key. Fill in one `struct rsi_hive` per hive your source backs:

```c
struct rsi_hive hive = {
    .name     = "MyStore",
    .name_len = 7,
    .flags    = 0,                    /* global hive */
    .root_guid = { /* 16-byte GUID of the hive root key */ },
    /* scope_guid left zero for a global hive */
};
```

The two decisions per hive:

- **Global or private?** A **global** hive (`flags = 0`, `scope_guid` zero) is visible system-wide. A **private** hive (`flags = RSI_HIVE_PRIVATE`, `scope_guid` non-zero) is scoped — only tokens carrying that scope GUID in their [LCS credentials](~peios-sdk/reference/token#lcs-registry-credentials) can resolve it. Use a private hive for per-application or per-tenant state that shouldn't be system-visible.
- **The root GUID.** Every hive is anchored at a root key identified by `root_guid`. This is the GUID paths in the hive resolve from, and it must match the root your storage actually holds.

## Register

Hand the kernel your hive array and the highest sequence number you've already persisted:

```c
int src = rsi_register(&hive, 1, /*max_sequence=*/0);
if (src < 0) {
    perror("rsi_register");   /* EPERM if you lack SeTcbPrivilege */
    return -1;
}
/* `src` is the source fd — serve the RSI protocol on it. */
```

Two things to get right:

- **`SeTcbPrivilege` is required.** Registration is a trusted operation; without the privilege you get `EPERM`. Sources run as trusted system components.
- **`max_sequence` is your durability contract.** It is the highest sequence number this source has *already persisted*. The kernel resumes its global sequence counter past it, so it never hands out a number you've used. A brand-new source with no stored state passes `0`; a source restarting with durable data must scan that data for the highest sequence it ever wrote and pass *that*. Getting this wrong risks sequence reuse, so make it the first thing your restart path computes.

You can register several hives in one call by passing an array and a `count` greater than one; the kernel enforces its configured `MaxHivesPerSource` limit (`ENOSPC` if you exceed it).

## After registration

The returned fd *is* your serve endpoint — you `read(2)` requests and `write(2)` responses on it directly (via the [request](~peios-sdk/reference/rsi-request) and [response](~peios-sdk/reference/rsi-response) helpers). Closing it deregisters the source and signals EOF to the kernel. Keep it open for the life of the source, and move on to the [serve loop](~peios-sdk/registry-sources/serving-requests).

## Next

- **[Serving requests](~peios-sdk/registry-sources/serving-requests)** — the loop that runs on the source fd.
- **[`rsi/source.h` reference](~peios-sdk/reference/rsi-source)** — every field and error.
