---
title: System Service Libraries
type: concept
description: Which C library, and matching Rust crate, to use for resolvd, timed, or trustd, or for reading registry documents, registry manuals, and event catalogs.
related:
  - peios/service-libraries/using-libresolvd
  - peios/service-libraries/using-libtimed
  - peios/service-libraries/using-libtrust
  - peios/service-libraries/utility-libraries
---

Peios system services publish C libraries so that your application can ask
them for their state, or ask them to act, without starting a command and
reading its output. Each library has a Rust crate that wraps the same shared
library. For access control, the registry, and events, use the
[Peios SDK](~peios/sdk-basics/what-is-the-peios-sdk) instead. For sign-in and
account operations, use the
[authentication client](~peios/authentication-client/conversations).

## Choosing a library

Choose the library for the service or format you need:

| Library | Use it to | Rust crate | Guide |
|---|---|---|---|
| `libresolvd` | Look up names and addresses, read resolver status, and flush the cache | `resolvd-client` | [Using libresolvd](~peios/service-libraries/using-libresolvd) |
| `libtimed` | Read clock status and sources, follow clock changes, and request time changes | `timed-client` | [Using libtimed](~peios/service-libraries/using-libtimed) |
| `libtrust` | Read and follow the trusted root certificates, and add or distrust certificates | `trust-client` | [Using libtrust](~peios/service-libraries/using-libtrust) |
| `libreg`, `libregman`, `libevman` | Parse registry documents, registry manuals, and event catalogs | `peios-reg`, `peios-regman`, `peios-evman` | [Utility Libraries](~peios/service-libraries/utility-libraries) |

`libresolvd`, `libtimed`, and `libtrust` talk to a running service. The
utility libraries work on documents and need no service.

## What the service decides

The service, not the library, decides what each call can do. It checks the
caller's permissions for the operation, so a call can be refused even when the
library loads and connects. A management call, such as adding a trusted
certificate or flushing the resolver cache, uses your own rights; the library
never raises them.

Each library's major version is part of its shared-library name, such as
`libresolvd.so.1`. A new major version means an incompatible C interface, so
link against the major version your code was written for.
