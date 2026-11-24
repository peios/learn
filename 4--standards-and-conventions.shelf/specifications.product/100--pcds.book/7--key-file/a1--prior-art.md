---
title: Prior Art
description: Where the key file sits against encrypted PKCS #8 and PEM key files, and which of their choices it keeps.
---

## PKCS #8 and PEM

An encrypted PKCS #8 file (RFC 5958) holds only the private key, under a
passphrase, and says nothing readable about which key it is until it is
opened. A key file keeps PKCS #8 for the private key, so that any
library can parse it once opened, and puts the public key and the
algorithm in front of it in the clear, so that a program can show which
key a file holds, or find the one it needs, without asking for a
passphrase.

## Design influences

**One format, whatever protects the key.** A key kept by a service under
access control and a key sealed on removable media share a layout, so an
export is the same key in a different protection, not a different format.

**Readable, not trusted.** The header is there to describe the key, and
never decides what is opened: the private key is checked against it.
