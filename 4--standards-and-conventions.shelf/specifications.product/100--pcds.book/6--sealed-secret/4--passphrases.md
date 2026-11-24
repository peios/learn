---
title: Passphrases
description: How typed text becomes a passphrase's bytes — Unicode NFKC, then UTF-8 — and the 15-character minimum for a passphrase that seals.
---

A sealed secret is opened by the same bytes that sealed it. Where a
passphrase is typed or read as text, two programs agree on its bytes
only if they turn text into bytes the same way.

A program that takes a passphrase as text MUST normalize it to Unicode
Normalization Form KC (NFKC, UAX #15) and use the UTF-8 encoding of the
result as the passphrase's bytes, both to seal and to open.

A program that seals a secret under a passphrase given as text MUST
refuse one shorter than 15 characters, counted as Unicode scalar values
of the normalized text. A program MUST NOT apply any strength rule when
it opens a sealed secret.

> [!NOTE]
> The same characters can be encoded more than one way: an accented
> letter can be one code point or a letter followed by a combining
> accent, depending on the keyboard and system. NFKC makes them one, so
> a passphrase typed on another machine still opens what it sealed.
> Fifteen characters is NIST SP 800-63B-4's minimum for a password used
> on its own. A sealed secret can be attacked offline by anyone who
> copies it, with nothing to limit their guesses, so length is what
> protects it; Argon2id only makes each guess slower.
