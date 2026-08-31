---
title: The trust command
type: reference
description: Every verb of the trust command — what it reads, what it writes, and what its exit statuses mean.
related:
  - peios/trust/overview
  - peios/trust/adding-and-distrusting
---

`trust` is the trust store's operator command. It **reads over trustd's
socket and writes to the registry**, and the asymmetry is worth
understanding: only trustd knows the *effective* set, because the shipped
roots are package data rather than registry entries, so a listing read from
the registry would show a handful of local decisions and none of the
hundred and fifty roots actually in force. Writes go the other way, to the
registry, so that `trust` and `reg` pass through the same access check.

## Verbs

| Command | Reads | Writes |
|---|---|---|
| `trust list [--purpose P]` | socket | — |
| `trust list --distrusted` | registry | — |
| `trust show <fingerprint> [--pem]` | socket | — |
| `trust status` | socket | — |
| `trust add <name> <file\|-> [--purposes A,B]` | the file | registry |
| `trust remove <name>` | — | registry |
| `trust distrust <fingerprint\|file> [--reason R]` | socket, then | registry |
| `trust restore <fingerprint>` | registry | registry |
| `trust reload` | — | — (asks trustd to recompose) |

## Listing

```
$ trust list
018e13f0772532cf  shipped    CN=DigiCert TLS ECC P384 Root G5,O=DigiCert\, Inc.,C=US
0a81ec5a929777f1  shipped    CN=GlobalSign,O=GlobalSign,OU=GlobalSign Root CA - R3
4f2ab19c8e10dd77  added:corp-ca  CN=Corp Issuing CA,O=Example Ltd,C=GB

121 root(s)
```

The first column is the first sixteen characters of the SHA-256
fingerprint, and every verb that takes a fingerprint accepts that prefix —
what is printed can be pasted back in. An ambiguous prefix is refused
rather than guessed at.

`--purpose ServerAuth` narrows the listing to roots carrying that purpose.

## Showing one root

```
$ trust show 4f2ab19c
subject      CN=Corp Issuing CA,O=Example Ltd,C=GB
fingerprint  4f2ab19c8e10dd77…
source       added
added as     corp-ca
purposes     ServerAuth
expires      2074003199

-----BEGIN CERTIFICATE-----
…
```

`--pem` prints the certificate alone, for piping into a file or another
tool.

## Exit statuses

| Status | Meaning |
|---|---|
| `0` | Done. |
| `2` | Asked about something that is not there — no root matches, no such addition, not distrusted. |
| `1` | It went wrong: the daemon is unreachable, the file is not a certificate, the registry refused the write. |
| `64` | The command line was not understood. |

The separation of `2` from `1` is what lets a script tell "this machine
does not trust that CA" from "I could not find out".

## When a write is refused

```
$ trust distrust 018e13f0772532cf
trust: not permitted to change Machine\System\Trust\Certificates\Distrust —
       changing what this machine trusts is governed by that key's descriptor
```

`trust` has no privilege of its own to grant. Changing the machine's trust
is a registry write, and whether you may make it is decided by the key's
security descriptor — the same answer `reg` would get.
