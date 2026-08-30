---
title: Signature Format
description: The fixed 3310-byte signature blob — where it is stored, the lookup order, what is covered, and how a key is selected and trusted.
---

## The blob

A signature is a fixed 3310-byte blob, identical wherever it is
stored:

| Offset | Size | Field |
|---:|---:|---|
| 0 | 1 | Version. MUST be `0x01`. |
| 1 | 3309 | Raw ML-DSA-65 signature. |

Total 3310 bytes exactly. There is no length field, no algorithm
identifier, no key identifier, no timestamp and no padding. A blob of
any other length MUST be rejected, and so MUST a version byte other
than `0x01`.

Signers MUST NOT emit any other version. A verifier encountering one
MUST treat the file as unsigned rather than attempting a fallback
interpretation.

## Storage

Two locations are defined. A verifier MUST consult them in this order.

### ELF section

An ELF binary SHOULD carry its signature in a section named exactly
`.peios.sig`. The name comparison covers all eleven bytes including
the terminating NUL, so a longer name having `.peios.sig` as a prefix
MUST NOT match.

The section's type MUST be `SHT_PROGBITS` and its size MUST be exactly
3310. The range `[sh_offset, sh_offset + sh_size)` MUST lie entirely
within the file.

The containing file MUST be `ELFCLASS64`, MUST be `ELFDATA2LSB`, and
MUST carry `EV_CURRENT` in `e_ident[EI_VERSION]`. `e_shentsize` MUST
equal 64. `e_shstrndx` MUST NOT be `SHN_UNDEF` and MUST be less than
`e_shnum`. The section header table and the section-name string table
MUST both lie entirely within the file.

No alignment or flag requirement applies. `sh_addralign`, `sh_flags`,
`sh_addr`, `sh_link` and `sh_info` are not inspected, and the
section's index and position are unconstrained. Where several sections
share the name, the one at the lowest index is used.

A 32-bit or big-endian ELF cannot carry a signature at all: it fails
the structural requirements above, and a verifier MUST NOT fall back
to the extended attribute for it.

### Extended attribute

Any file MAY carry its signature in the extended attribute
`security.peios.sig`. The value MUST be exactly 3310 bytes; any other
size MUST be treated as unsigned.

This is the only location available to non-ELF files, and it is
available to ELF files that carry no `.peios.sig` section header.

An extended attribute is a property of an inode, not of the file's
bytes, so a signer cannot ship one: it produces the blob and something
with the right to set `security.*` attributes on the destination
filesystem applies it when the file is created. On Peios that is the
package consumer, from a detached-signature payload entry named
`<file>.peios.sig` (PSPU §5.16). A signer that emits the blob under
that name beside the file it signs, and does not touch the file, has
done its whole job for this placement.

### Lookup order and commitment

A verifier MUST determine the storage location as follows.

1. Read the first four bytes. A file shorter than four bytes, or whose
   first four bytes are not `\x7fELF`, is not ELF: go to step 3.
2. Parse the ELF structures and scan for a section named
   `.peios.sig`. **Once such a section header is found, the ELF path
   is committed**: the extended attribute MUST NOT be consulted,
   whatever happens next. A wrong type, a wrong size, an out-of-range
   offset, a read failure, a bad version byte or a failed verification
   all yield "unsigned". A structural failure encountered while
   parsing MUST commit the path in the same way. The single exception
   is `e_shnum == 0`, which does not commit.
3. Read `security.peios.sig`. If present and exactly 3310 bytes, use
   it.
4. Otherwise the file is unsigned.

The commitment rule is a security requirement rather than an
optimisation. Without it, an attacker able to write a malformed ELF
section could force fallback to whichever location they more easily
controlled.

Where both locations are populated, the ELF section wins. A signer
SHOULD NOT populate both.

## What is signed

The message is a 32-byte SHA-256 content hash. Which bytes it covers
depends on where the signature is stored, and a signer MUST use the
form matching its chosen location.

**ELF section source.** The hash covers the file with the section's
*contents* replaced by zeros:

```
SHA-256( file[0 .. sh_offset)
       || 0x00 × sh_size
       || file[sh_offset + sh_size .. file_size) )
```

Only the section **contents** are zeroed. The `Elf64_Shdr` entry
describing the section is hashed verbatim, as are the ELF header, the
program headers, the section-name string table and every other byte of
the file. The section header metadata is therefore integrity-protected
along with everything else, which is what stops an attacker relocating
or resizing the signature section without invalidating the signature.

This has a direct consequence for how a signer MUST work. The complete
file layout — including `sh_offset`, `sh_size`, `sh_name` and the
position of the section header table — MUST be final before the hash
is computed. The practical sequence is to reserve a 3310-byte
`.peios.sig` section filled with zeros, finalise the layout, hash the
file as it then stands, sign the hash, and write the blob into the
reserved bytes without touching anything else. Because the reserved
region is already zero, the file as hashed and the file as shipped
differ only in those 3310 bytes.

**Extended attribute source.** The hash covers the entire file with no
exclusions:

```
SHA-256( file[0 .. file_size) )
```

This applies to ELF files reaching the attribute path as well as to
non-ELF ones. The ELF-zeroed form is used **only** when the ELF
section is the signature source.

In both cases `file_size` is a snapshot taken at the start of
verification. A verifier MUST re-check the size before returning and
MUST discard the result if it changed.

## Algorithm

The signature is **ML-DSA-65** as specified in FIPS 204. The public
key is 1952 bytes and the signature is 3309 bytes.

Signing is:

```
ML-DSA.Sign(private_key, content_hash, ctx = "")
```

and verification is the corresponding `ML-DSA.Verify`.

This is **pure** ML-DSA — FIPS 204 Algorithm 2 and Algorithm 3 — and
not HashML-DSA, the pre-hashing variant. The message happens to be a
32-byte SHA-256 hash, which pure ML-DSA signs directly. A signer MUST
NOT use the pre-hashing variant; a signature produced that way will
not verify.

The context string MUST be empty. Signers MUST NOT set a context.
Verifiers cannot express one, so a signature produced under a
non-empty context simply fails to verify rather than being detected
and reported.

It follows that ML-DSA's context field is **not** available for domain
separation between binary signatures and any other Peios signature
system. Separation MUST come from using distinct keys.

A signer MUST supply the public key as the **raw** 1952-byte key, not
an SPKI-wrapped DER encoding. From OpenSSL 3.5 or later, the raw key
is the trailing 1952 bytes of the DER public key.

## Key selection and trust tiers

The blob carries no key identifier, so a verifier selects a key by
exhaustive trial: it tries each key in its table in order and takes
the first that verifies.

The trust tier is a property of **which key verified** — a `pip_type`
and a `pip_trust`, both unsigned integers — and never of anything the
signer encoded. A signer cannot express intent about the tier it
wants. It obtains whichever tier the verifier associates with the key
it used, and if the verifier carries no matching key the file is
simply unsigned.

Consequently:

- A signer that wants software to run at a tier MUST have its public
  key present in the verifier's table. Getting a key into that table
  is a deployment question, not a format question.
- A signer MUST NOT assume its signature is portable across systems
  carrying different key tables. The same file may be trusted on one
  and untrusted on another, with no observable difference in the file.
- Verification cost is linear in the number of keys, so a verifier MAY
  reasonably carry few.
