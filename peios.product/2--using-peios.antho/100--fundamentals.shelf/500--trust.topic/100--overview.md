---
title: The trust store
type: concept
description: What a Peios machine trusts when it validates a certificate — Mozilla's roots as package data, additions and distrusts as registry decisions, composed by trustd and rendered to /etc/ssl.
related:
  - peios/trust/the-trust-command
  - peios/trust/adding-and-distrusting
  - peios/linux-compatibility/name-service-switch
  - peios/registry-administration/regman
---

When a program on this machine validates a TLS certificate, the set of
certificate authorities it will accept comes from one place: **trustd**,
the trust store.

trustd composes that set from two inputs and serves the result.

| Input | Where it lives | Who changes it |
|---|---|---|
| Mozilla's root store | `/usr/share/ca-certificates/mozilla.crt`, shipped by the `ca-certificates` package | An upgrade of that package |
| Additions and distrusts | `Machine\System\Trust\Certificates` in the registry | An administrator, or the domain |

The split is the whole design. The roots are **package data** — a hundred
and twenty-odd certificates nobody on this machine decided anything about
— and package upgrades already do the right thing with them, including
removing a root Mozilla has withdrawn. The registry holds **decisions**:
each entry is something somebody chose, which is what keeps an audit of
`Machine\System\Trust` worth reading.

## What programs actually read

The store itself is a socket, `/run/trustd/trust.sock`. Peios-native
programs ask it directly and are told when the answer changes, so a
certificate withdrawn at ten past three stops being accepted by a running
service at ten past three.

Almost nothing does that yet, so trustd also *renders* the store to the
files the portable software ecosystem expects:

```
/etc/ssl/certs/ca-certificates.crt   the bundle Go and most software read
/etc/ssl/cert.pem                    OpenSSL's default CAfile
/etc/ssl/certs/<hash>.0              OpenSSL's default CApath
```

Those files are a **copy of an answer**, not the answer. Editing one
changes nothing: trustd overwrites it the next time anything changes. The
`GenerateLinuxTrustFiles` value decides whether they exist at all — see
[the compat files](~peios/trust/the-compat-files).

> [!NOTE]
> There is no `update-ca-certificates` and no directory to drop a `.crt`
> into. Both exist on other systems because trust policy lives in files
> there; here it lives in the registry, where changing it is an access
> check against a key's descriptor rather than a question of who can write
> to a directory.

## Seeing what is in force

```
$ trust status
generation   7
health       ok
roots        121 in force
  shipped    121
  added      0
  distrusted 0
compat       GenerateLinuxTrustFiles = 1
  rendered   /system/retc/ssl/certs/ca-certificates.crt
  rendered   /system/retc/ssl/cert.pem
```

`generation` increases every time the store changes, so a program holding
a copy can tell whether it is current without fetching it again.
`health` is `degraded` when the last composition failed — see
[when the store is degraded](~peios/trust/adding-and-distrusting).

## Composition is all or nothing

If the shipped bundle cannot be read, or yields implausibly few roots, or
every root would be distrusted, trustd **keeps whatever it rendered last**
and reports itself degraded. It never writes a partial store.

That is deliberate, and the reasoning is worth stating: a silently empty
trust store breaks every TLS client on the machine at once, and a silently
truncated one might be missing the distrust that was the point of the last
change. Stale-but-whole is a recoverable state; partial is not.

A single bad *entry* is different. An addition that is not a certificate,
is not a CA, or has expired is skipped with a warning and everything else
proceeds — one administrator's typo does not take the machine's trust
down.

## Who may change it

`Machine\System\Trust\Certificates` and its subkeys, like any registry
key, are governed by their own security descriptor. By default SYSTEM and
Administrators may write; everybody may read. That descriptor is the
*only* gate: [`trust`](~peios/trust/the-trust-command) and `reg` write the
same values through the same check, so there is no second permission model
to keep in step with the first.

Reading is open to everyone, because the root set is public — in the
default configuration it is sitting in a world-readable file.

## What trustd is not

**It holds no private key.** Not the machine's, not anybody's. A service
that holds keys is a signing oracle if it is ever compromised, and wants
almost the opposite security posture from one whose socket is open to
every program on the machine. Machine identity — the certificates and keys
a machine presents when *it* is the server — is a separate concern, and
will be a separate service.

**It does not fetch anything.** No root is downloaded on demand and no
revocation list is retrieved, in this version. What the machine trusts
changes when a package is upgraded or somebody writes to the registry, and
at no other time.
