---
title: Carrying a Bundle
description: The three places a bundle is carried, an ELF section, an
  extended attribute, and a detached file, the bytes each covers, and the
  order a verifier looks in them.
---

A bundle is carried in one of three places. The bundle's bytes are the
same in each.

| Place | Name | For | Hash form |
|---|---|---|---|
| ELF section | `.pso` | An ELF object | `0x02` |
| Extended attribute | `security.pso` | Any file | `0x01` |
| Detached file | `<file>.pso`, beside the file | Any file, where a consumer says so | `0x01` |

## Hash forms

A leaf's `hash_form` says which bytes of the file its `content_hash`
covers. The enumeration is closed (§7.15).

**`0x01`, whole file.** The hash covers every byte of the file.

**`0x02`, ELF.** The hash covers the file with the contents of its
`.pso` section replaced by zeros. If the file also has a `.peios.sig`
section (PSPK §3.2), its contents are replaced by zeros as well. Only
section contents are replaced: the section headers, and every other byte
of the file, are hashed as they are.

A verifier MUST require the hash form the place calls for, and MUST
report a leaf with any other as invalid. A bundle moved from one place
to another does not verify.

> [!NOTE]
> A file that carries both `.pso` and `.peios.sig` is one that has to
> verify under this chapter and under the older format at once. Each
> signature would otherwise cover the other. A signer avoids the
> circle by adding the bundle first, with both sections zeroed, and the
> older signature second, over the result.

## The ELF section

An ELF object SHOULD carry its bundle in a section named exactly `.pso`.
The name comparison covers the terminating NUL, so a longer name with
`.pso` as a prefix does not match. Where several sections have the name,
the one at the lowest index is used.

The section's type MUST be `SHT_PROGBITS`, and its range MUST lie within
the file. The file MUST be `ELFCLASS64` and `ELFDATA2LSB`, with
`e_shentsize` equal to 64 and a valid `e_shstrndx`.

A signer reserves the section at its final size before it hashes,
because the section headers are covered. The size is known in advance:
every field of a bundle has a length the signer can compute before it
signs.

## The extended attribute

Any file MAY carry its bundle in the extended attribute `security.pso`.
This is the only place for a file that is not ELF, short of a detached
file.

An extended attribute belongs to the file as stored, not to its bytes,
so a signer cannot ship one. A signer writes the bundle as a detached
file, and whatever installs the file sets the attribute from it. For a
package, that is PSPU §5.16.

## The detached file

A detached bundle is a file named for the file it covers, with `.pso`
added, in the same directory. A verifier looks for one only when the
consumer asks it to, as a consumer that fetches signed metadata does.

## Lookup order

A verifier asked about a file, and not told where the bundle is, MUST
find it as follows:

1. If the file begins with `7f 45 4c 46`, read its ELF structures and
   look for a `.pso` section. If the section header is found, the bundle
   is the section's contents, and the extended attribute is not
   consulted, whatever happens next.
2. Otherwise, read `security.pso`. If it is present, it is the bundle.
3. Otherwise, the file has no bundle.

A failure after the section header is found, such as a wrong type, a
range outside the file, or a malformed bundle, makes the result invalid.
It does not send the verifier to the extended attribute.

> [!NOTE]
> Without this commitment, a party able to damage the section could
> choose which of the two places the verifier believed, and would
> choose the one it controlled.

A file with no bundle is not invalid. It is unsigned, which §7.14
reports as its own result.
