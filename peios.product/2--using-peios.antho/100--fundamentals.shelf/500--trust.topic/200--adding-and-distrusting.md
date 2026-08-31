---
title: Adding and distrusting certificates
type: how-to
description: Trust a certificate authority the shipped set does not include, stop trusting one it does, and understand what happens when the store cannot be composed.
related:
  - peios/trust/overview
  - peios/trust/the-trust-command
  - peios/registry-administration/regman
---

Two things can be decided about this machine's trust, and both are values
under `Machine\System\Trust\Certificates`.

## Trusting a certificate authority

An internal CA, a test CA, a partner's CA:

```
$ trust add corp-ca /path/to/corp-root.pem
added corp-ca
  CN=Corp Issuing CA,O=Example Ltd,C=GB
  SHA-256 4f2a…c19b
```

The name is yours to choose — it names the *decision*, not the
certificate, so `corp-ca` is a better name than `4f2a`. PEM or DER is
accepted; a file holding more than one certificate is refused, because a
bundle added under one name would be one decision covering several
authorities.

The certificate is checked before it is written: it must parse, it must be
a CA (`basicConstraints`), and it must not have expired. trustd checks it
again when it reads it — it never trusts the writer — but doing it here
means a mistake is a message rather than a line in a log.

To undo:

```
$ trust remove corp-ca
```

### Purposes

By default an addition is trusted for `ServerAuth` — validating a TLS
server. Say otherwise if you mean otherwise:

```
$ trust add corp-ca corp-root.pem --purposes ServerAuth,CodeSigning
```

This version renders `ServerAuth` roots and carries the rest, so a root
recorded for another purpose is stored faithfully and used when the
feature that consumes it arrives.

## Distrusting a certificate authority

This is the one that has to work in a hurry, and it works on any
certificate — one Mozilla shipped or one somebody added:

```
$ trust distrust 018e13f0772532cf --reason "withdrawn, see CA/B incident 2026-08"
distrusted 018e13f0772532cf809bd1b17281867283fc48c6e13be9c69812854a490c1b05
  was: CN=DigiCert TLS ECC P384 Root G5,O=DigiCert\, Inc.,C=US
```

Within a second or two the root is gone from the store, gone from the
rendered bundle, and its file is gone from the hashed directory. Nothing
is rebuilt and nothing is rebooted, which is the reason the shipped roots
can be package data in the first place: **withdrawal never waits for a
package**.

A certificate is named by its SHA-256 fingerprint — never by subject name,
which is forgeable and reused. Any of these work:

```
018e13f0772532cf                      the prefix `trust list` prints
018E13F0…C1B05                        upper case
01:8e:13:f0:…                          colon-separated, as other tools print it
/path/to/the-certificate.pem          the file itself
```

Distrusting a certificate this machine does not have is legitimate and is
recorded rather than refused — the entry sits there, and if that root ever
arrives in a bundle upgrade or an addition, it is already refused.

To see what has been decided, and to undo it:

```
$ trust list --distrusted
018e13f0772532cf  withdrawn, see CA/B incident 2026-08

1 distrusted

$ trust restore 018e13f0772532cf
restored 018e13f0772532cf809bd1b17281867283fc48c6e13be9c69812854a490c1b05
```

## Doing it from the registry

`trust` writes registry values and nothing else, so `reg` does the same job
and is subject to exactly the same access check:

```
Machine\System\Trust\Certificates\
  Add\<name>\
    Certificate   REG_BINARY    the certificate, DER
    Purposes      REG_MULTI_SZ  default ServerAuth
  Distrust\
    <fingerprint> REG_SZ        why, for whoever reads it later
```

Write `Certificate` **last** when creating an entry by hand. Until it
exists the entry is incomplete, and trustd deliberately skips incomplete
entries rather than acting on half of one.

This is also how a domain distributes trust: pushing a value to
`Trust\Certificates\Add` on every member is an ordinary policy write, not
a special mechanism.

## Packages may offer trust, never take it

A package must never widen what the whole machine trusts by being
installed — `peipkg install` quietly adding a CA is a supply-chain hole,
and every system that allowed it eventually closed it.

A package that comes with a CA ships a *seed* (`/usr/share/regim/…`),
inert until an image names it in `[registry] autoapply` or an
administrator applies it. Installing the package grants nothing.

A package shipping a trust store for **its own** private use — a browser,
a language runtime — is unaffected by any of this. Those are ordinary
files that only that program reads.

## When the store is degraded

```
$ trust status
health       degraded — cannot read /usr/share/ca-certificates/mozilla.crt: …
```

`degraded` means the last attempt to compose the store failed, and what is
rendered is what was rendered before — possibly stale, never partial. The
machine keeps working with the trust it last had.

The usual causes are a missing or damaged `ca-certificates` package, or a
distrust list that would empty the store entirely. Fix the cause and:

```
$ trust reload
```

Skipped entries are different and are not a degraded state: `trust status`
counts them and the log names each one.
