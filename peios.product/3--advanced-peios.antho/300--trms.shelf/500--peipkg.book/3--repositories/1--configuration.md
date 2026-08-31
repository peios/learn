---
title: Configuration
description: A repository is a file naming a base URL and the policy applied to it — the local handle and the transport it uses.
---

A repository is configured by a file naming its base URL and the policy
peipkg applies to it.

| Setting | Meaning |
|---|---|
| Base URL | Where the descriptor and everything it points at are served from |
| Trust anchors | Expected key fingerprints, supplied out of band |
| Signature policy | `required` or `optional` (PSPU §5.37) |
| Priority | A positive integer; lower is higher priority |
| Minimum index version | The out-of-band freshness floor applied at first add |
| Maximum trusted age | How long a repository's trust state stays usable without a refresh |
| Insecure transport | Whether a non-HTTPS base URL is permitted for this repository |
| Allow SD overrides | Whether packages from here may declare security descriptors (PSPU §5.20) |

The default signature policy for a new repository is `required`. The
default maximum trusted age is 30 days. The default priority is the same
for every repository, including the official one, so the ordering the
resolver applies is whatever the operator configured rather than
something peipkg assumes.

An explicit maximum trusted age of zero is rejected rather than treated
as "use the default", so that a mistyped value cannot silently disable
the freshness check.

## The local handle

A repository has a name in the descriptor and a handle in the local
configuration. They are conventionally the same, and nothing requires
them to be: peipkg identifies a repository internally by the local
handle, and compares an index's declared repository name against the
**descriptor's** name, which it records when it verifies the descriptor.

Comparing against the handle instead made a configuration whose handle
differed from the descriptor's name add successfully, write a valid
cache, and then fail its cached-index check on every later operation —
permanently, and with the repository dropped from resolution.

A repository recorded before the descriptor name was kept — or one in
unsigned mode, whose descriptor was never verified — has none to compare
against, and falls back to the handle it was recorded under.

## Transport

A base URL is HTTPS unless the repository's insecure-transport setting
permits otherwise. The setting is per-repository; there is no global
form.

`file://` base URLs are accepted for local development. They are exempt
from the transport check rather than gated by it, so a repository on
removable or network-mounted media is added without the operator
acknowledging the transport.

Changing the insecure-transport setting after a repository has been
added means editing its configuration file. There is no verb for it, and
so no prompt and no audit event accompanies the change.

## Allowing security-descriptor overrides

A package may declare a security descriptor for an entry it ships, and
the format cannot check that its producer had any authority over the
principals that descriptor grants access to. §5.20 makes that the
consumer's judgement, so it is configured per repository.

It defaults to **off**, and a package carrying overrides from a
repository that has not been vouched for is refused outright rather than
installed with the overrides dropped. A repository whose packages
legitimately ship descriptors — the system's own, above all, since
`fsbase` is what declares the descriptors for `/home` and `/tmp` —
must say so:

```toml
allow_sd_overrides = true
```

The default fails towards less authority, which is the direction that
shows: an install stops and says why. Failing the other way would let a
repository nobody had thought about set access control on the machine,
and nothing would report it.
