---
title: Checksum commands
type: reference
description: md5sum, sha1sum, sha256sum and the rest — the family of commands that each compute and verify one fixed hash algorithm.
related:
  - peios/hashing-and-encoding/cksum
  - peios/hashing-and-encoding/overview
---

This page covers a family of commands that all work the same way and differ only in **which hash algorithm** they use:

| Command | Algorithm | Digest size |
|---|---|---|
| `md5sum` | MD5 | 128-bit |
| `sha1sum` | SHA-1 | 160-bit |
| `sha224sum` | SHA-224 | 224-bit |
| `sha256sum` | SHA-256 | 256-bit |
| `sha384sum` | SHA-384 | 384-bit |
| `sha512sum` | SHA-512 | 512-bit |
| `b2sum` | BLAKE2b | up to 512-bit |

```
sha256sum [options] [file...]
```

Everything below is written with `sha256sum`, but applies to every command in the table.

## Computing a checksum

Run plainly, the command prints the hash of each file, followed by the file name:

```
$ sha256sum installer.iso
9f86d0818884...b1a5  installer.iso
```

With no file, it reads standard input. The hash is a fingerprint of the file's contents: change a single byte and the hash changes completely.

## Verifying with a checksum

The everyday use is **verification** — confirming a file is exactly what it should be, usually a download.

First, the file's publisher computes a checksum and publishes it, often in a file:

```
$ sha256sum installer.iso > installer.iso.sha256
```

Then anyone with the file and that checksum file can verify:

```
$ sha256sum -c installer.iso.sha256
installer.iso: OK
```

`-c` reads each `hash  filename` line, recomputes the hash, and reports `OK` or `FAILED`. A `FAILED` means the file is not the one the checksum was made from — corrupted in transit, or altered.

| Option | Effect |
|---|---|
| `-c`, `--check` | Read checksums from the given files and verify them. |
| `--ignore-missing` | In check mode, do not fail over files that are listed but absent. |
| `--quiet` | In check mode, print nothing for files that pass — only failures. |
| `--status` | In check mode, print nothing at all; report only through the exit status. |
| `-w`, `--warn` | Warn about improperly formatted lines in the checksum file. |
| `--strict` | In check mode, fail if any checksum line is malformed. |

## Output format

| Option | Effect |
|---|---|
| `--tag` | Produce a tagged line — `SHA256 (file) = hash` — that records which algorithm was used. |
| `--untagged` | Produce the plain `hash  file` line. This is the default. |
| `-z`, `--zero` | End each output line with a NUL character instead of a newline. |
| `-b`, `--binary` | Note the file as read in binary mode. |
| `-t`, `--text` | Note the file as read in text mode. |

`b2sum` additionally accepts `-l`, `--length=BITS` to produce a shorter BLAKE2b digest.

## A note on choosing an algorithm

These commands detect change — but not all of them resist a *deliberate* attempt to forge a match. MD5 and SHA-1 can be defeated by an attacker who wants two different files to share a checksum. They are still fine for catching accidental corruption, but for verifying that a file has not been **tampered with**, use a SHA-2 command (`sha256sum` and up) or `b2sum`.

## Exit status

| Code | Meaning |
|---|---|
| `0` | The checksums were computed, or — in check mode — every file verified. |
| `1` | In check mode, a file failed verification. |
| `2` | An error — a file could not be read, or a checksum file was malformed. |
