---
title: cksum
type: reference
description: The general checksum tool — compute or verify a digest with any of the supported algorithms.
related:
  - peios/hashing-and-encoding/checksum-commands
  - peios/hashing-and-encoding/overview
---

`cksum` is the **general** checksum command. Where each of the [checksum commands](~peios/hashing-and-encoding/checksum-commands) is fixed to one algorithm, `cksum` does any of them — the algorithm is an option.

```
cksum [options] [file...]
```

```
$ cksum installer.iso
3915528286 372736000 installer.iso
$ cksum -a sha256 installer.iso
9f86d0818884...b1a5  installer.iso
```

With no `-a`, `cksum` computes a CRC checksum and prints the CRC value, the file's byte count, and the name. With `-a`, it behaves like the corresponding dedicated command.

## Choosing the algorithm

| Option | Effect |
|---|---|
| `-a`, `--algorithm=NAME` | Use the named algorithm. |

`NAME` may be:

| Name | Algorithm |
|---|---|
| `crc` | The default CRC. |
| `crc32b` | A CRC-32 variant. |
| `md5` | MD5 — as `md5sum`. |
| `sha1` | SHA-1 — as `sha1sum`. |
| `sha224`, `sha256`, `sha384`, `sha512` | The SHA-2 family — as the matching `sha*sum`. |
| `sha3` | SHA-3. |
| `blake2b` | BLAKE2b — as `b2sum`. |
| `sm3` | The SM3 hash. |
| `sysv`, `bsd` | The legacy block checksums — as [`sum`](~peios/hashing-and-encoding/sum). |

`crc`, `crc32b`, `sha3`, and `sm3` are available *only* through `cksum` — there is no dedicated command for them.

## Verifying

`cksum` checks files the same way the dedicated commands do:

| Option | Effect |
|---|---|
| `-c`, `--check` | Read checksums and verify the files against them. |
| `--ignore-missing` | Do not fail over listed files that are absent. |
| `--quiet` | Print nothing for files that pass. |
| `--status` | Print nothing; report only through the exit status. |
| `-w`, `--warn` | Warn about malformed checksum lines. |
| `--strict` | Fail on a malformed checksum line. |

## Output format

| Option | Effect |
|---|---|
| `--tag` | Produce a tagged `ALGORITHM (file) = hash` line. The default for most algorithms. |
| `--untagged` | Produce a plain `hash  file` line. |
| `--raw` | Output the raw binary digest, with nothing else. |
| `--base64` | Print the digest in base64 rather than hexadecimal. |
| `-l`, `--length=BITS` | For an algorithm that supports it, produce a shorter digest. |
| `-z`, `--zero` | End each output line with a NUL character. |

## Exit status

| Code | Meaning |
|---|---|
| `0` | Success — or, in check mode, every file verified. |
| `1` | In check mode, a file failed verification. |
| `2` | An error — a file could not be read, or an option was invalid. |
