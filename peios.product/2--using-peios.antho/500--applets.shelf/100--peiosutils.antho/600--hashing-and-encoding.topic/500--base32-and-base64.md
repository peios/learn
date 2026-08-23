---
title: base32 and base64
type: reference
description: Encode binary data as text using the base32 or base64 alphabet, and decode it back.
related:
  - peios/hashing-and-encoding/basenc
  - peios/hashing-and-encoding/overview
---

`base32` and `base64` encode binary data as plain text — and decode it back. They are the same command with one difference: the **alphabet** they use.

```
base32 [options] [file]
base64 [options] [file]
```

```
$ echo Peios | base64
UGVpb3MK
$ echo UGVpb3MK | base64 -d
Peios
```

## What encoding is for

Some channels only carry text safely — they mangle or reject arbitrary bytes. Encoding rewrites binary data using a small, safe set of characters, so it can pass through unharmed; decoding reverses it exactly. `base64` uses 64 characters and is the more compact; `base32` uses 32 and is more robust where case might not survive. With no file, both read standard input.

Encoding is **not** encryption — anyone can decode the result. See the [overview](~peios/hashing-and-encoding/overview).

## Options

By default these commands *encode*. The options below apply identically to both.

| Option | Effect |
|---|---|
| `-d`, `--decode` | Decode instead of encode. |
| `-i`, `--ignore-garbage` | When decoding, skip any characters that are not part of the alphabet, rather than failing on them. |
| `-w`, `--wrap=COLS` | When encoding, wrap the output to lines of `COLS` characters. The default is 76; `-w 0` disables wrapping and produces one unbroken line. |

When decoding, newlines in the input are always tolerated; `-i` is for *other* stray characters.

## Exit status

| Code | Meaning |
|---|---|
| `0` | Success. |
| `1` | A file could not be read, or — when decoding — the input was not valid for the alphabet. |
