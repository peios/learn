---
title: The files under /etc/ssl
type: concept
description: Why the trust store is rendered to files at all, what each of the three artifacts is for, and what turning them off does.
related:
  - peios/trust/overview
  - peios/linux-compatibility/name-service-switch
---

The machine's trust store is a socket. The files under `/etc/ssl` are a
compatibility rendering of it, for software that reads trust from a path —
which today is very nearly all software.

They are generated. A manual edit lasts only until the next change, and a
header at the top of the bundle says so. Use [adding and
distrusting](~peios/trust/adding-and-distrusting) to change trust policy.
Use `trust status` to check whether these files are enabled and where they
were rendered.

## Three artifacts, because the ecosystem does not agree

| Path | Who reads it |
|---|---|
| `/etc/ssl/certs/ca-certificates.crt` | Go probes this first; most software is configured with it |
| `/etc/ssl/cert.pem` | OpenSSL's default `CAfile` on this system |
| `/etc/ssl/certs/<subject-hash>.0` | OpenSSL's default `CApath` |

The hashed directory is not decoration. OpenSSL looks a certificate up
there by a hash of its subject, and a stale file left behind for a root
that has been distrusted would go on being trusted through that path. So
the directory is replaced **atomically** — the new one is built alongside
and exchanged in a single operation — and there is no moment at which it
holds a mixture of the old set and the new.

## Turning them off

`Machine\System\Trust GenerateLinuxTrustFiles` decides whether the files
exist:

| Value | Effect |
|---|---|
| `1` (default) | Rendered and kept current. |
| `0` | No files. Programs that read a path find nothing and fail with certificate errors. |
| `2` | Reserved. Treated as `1`. |

`0` is the machine whose entire software set asks the socket — an
appliance image, in practice, where you know what is installed. On a
general-purpose system it breaks curl, Python, Go binaries and anything
else that reads a bundle, and the breakage looks like a certificate
problem rather than a configuration one, so set it deliberately.

Switching to `0` **removes** the rendered files rather than leaving them.
Stale trust left in force is worse than none: a root distrusted after the
switch would go on being accepted by everything reading the abandoned
copy.

```
$ reg set Machine/System/Trust GenerateLinuxTrustFiles dword:0
$ trust status
compat       GenerateLinuxTrustFiles = 0 (no files; the socket is the only store)
```

The socket keeps serving throughout — `trust list` still answers, and so
does any program that speaks to trustd directly.

In Security Policy, the **Certificate Files** switch under **Settings**
writes the same value. Turning it on applies at once; turning it off asks
first, since it breaks every program that reads a path.

To restore compatibility files after disabling them:

```
$ reg set Machine/System/Trust GenerateLinuxTrustFiles dword:1
$ trust status
```

Confirm `GenerateLinuxTrustFiles = 1`, the rendered paths, and `health` of
`ok`, then retry the affected program. If the store is degraded, follow
[the recovery steps](~peios/trust/adding-and-distrusting#when-the-store-is-degraded)
before relying on the rendered trust.

## Why a copy, when name resolution gets a pointer

`/etc/resolv.conf` on Peios is a constant file naming the resolver, and
nothing is ever generated into it. Trust cannot work that way: there is no
"ask over here" a certificate bundle can express. A file that lists
authorities has to *be* the list.

That is the whole difference between the two, and the reason this one
carries a knob and a warning while the other does not.

> [!NOTE]
> The rendered files come out readable by everyone, which is correct — the
> set of certificate authorities a machine trusts is not a secret, and
> every program on the machine needs it. What is protected is *changing*
> it, which is a registry write.
