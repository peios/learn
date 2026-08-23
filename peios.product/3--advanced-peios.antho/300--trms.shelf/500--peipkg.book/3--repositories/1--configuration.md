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
configuration. They are conventionally the same. peipkg identifies a
repository internally by the local handle, and compares an index's
declared repository name against that handle — so a configuration whose
handle differs from the descriptor's name produces a repository that
adds successfully and is then skipped at every install, with a warning
rather than an error.

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
