---
title: "signature.*"
description: "Every field the evman catalogue defines under signature: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `signature`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="signature.algorithm"></a>`signature.algorithm`

- **Type:** `str.enum`
- **Values:** `ml-dsa-65`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

The algorithm a signature was made with. Peios code signatures are
ML-DSA-65 over a SHA-256 digest of the file, and that is the only value
today; the set is open so that a second algorithm can be added.

**Carried by:**

No event carries this field yet.

## <a id="signature.crypto-stage"></a>`signature.crypto-stage`

- **Type:** `str.enum`
- **Values:** `alloc-transform` · `set-pubkey` · `boot-probe`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

Where the signature machinery failed, when verification could not run.
`alloc-transform` means the kernel could not obtain an ML-DSA-65
transform; `set-pubkey` that the transform rejected a key from the
built-in table, which is a fault in the table rather than a signature
that did not match; `boot-probe` that the one-off check made once the
crypto subsystem is up found the algorithm unavailable.

Each makes verification impossible rather than negative. The exec path
refuses a signed binary it cannot verify rather than run it unlabelled,
so a crypto failure shows as refused execs across the whole system.

**Carried by:**

- [`kacs.signature.crypto.failed`](~peios/events/kacs/kacs-signature-crypto-failed)

## <a id="signature.location"></a>`signature.location`

- **Type:** `str.enum`
- **Values:** `none` · `elf-section` · `xattr`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

Where a file's signature was found. `elf-section` is the `.peios.sig`
section of an ELF file, `xattr` the `security.peios.sig` extended
attribute, and `none` means the file carried neither and is unsigned. The
ELF section is looked for first; an ELF file whose headers are malformed
is not then checked for the attribute.

**Carried by:**

No event carries this field yet.

## <a id="signature.parse-error"></a>`signature.parse-error`

- **Type:** `str.enum`
- **Values:** `elf-magic-read` · `elf-short-ehdr` · `elf-ehdr-read` · `elf-bad-ident` · `elf-bad-shtable` · `elf-shdrs-range` · `elf-shstr-read` · `elf-strtab-range` · `elf-shdr-read` · `elf-name-read` · `elf-bad-sig-section` · `elf-bad-blob` · `elf-hash-fail` · `xattr-bad-blob` · `xattr-hash-fail` · `size-changed`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

Why the signature material on a file could not be read, named for its
`KACS_SIG_*` code. The `elf-` values are failures walking the ELF header
and section table to the `.peios.sig` section, or reading and hashing the
signature inside it; the `xattr-` values are the same for the
`security.peios.sig` attribute. `size-changed` is not a parsing failure:
the file changed size while it was being read, and the kernel discarded
what it had found.

**Every value leaves the file treated as unsigned.** The binary runs
without the integrity label its signature would have given it, so a
record carrying this field is the only thing that tells a damaged or
tampered signature from no signature at all.

**Carried by:**

No event carries this field yet.

## <a id="signature.result"></a>`signature.result`

- **Type:** `str.enum`
- **Values:** `unsigned` · `bad-key-table` · `no-key-match` · `verified` · `crypto-unavailable` · `crypto-mismatch`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

The outcome of checking a signature against the built-in signing keys,
named for its `KACS_SIG_*` code. `verified` means a key verified it and
the file takes that key's integrity tier; `no-key-match` that it was
signed but no built-in key verified it; `unsigned` that there was nothing
to check. `bad-key-table` and `crypto-unavailable` mean verification
could not run at all, and the exec path treats both as a refusal, never as
unsigned. `crypto-mismatch` is the result for one key that did not verify
the signature on the way to the next; the whole check then ends in
`verified` or `no-key-match`.

**`no-key-match` runs the binary unlabelled, exactly as `unsigned` does.**
It is a stronger signal than it looks: something was signed with a key
this system does not trust.

**Carried by:**

No event carries this field yet.

## <a id="signature.signing-key.fingerprint"></a>`signature.signing-key.fingerprint`

- **Type:** `bin`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

The fingerprint of a signing key: the SHA-256 digest of its public key,
the value the `kacs/signing_keys` listing shows as `key_sha256`. **Not
emitted today.** The verification path identifies a key only by its
position in the built-in table and never digests it, so nothing at the
point of decision can supply this value; `signature.signing-key.index` is
all a record carries. Until it is, a `no-key-match` verdict cannot say
which key a binary was expected to match.

**Carried by:**

No event carries this field yet.

## <a id="signature.signing-key.index"></a>`signature.signing-key.index`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

The zero-based position of a signing key in the kernel's built-in key
table, which is all that identifies a key at the point of verification
today. The table is compiled into the kernel, so an index means something
only against the same kernel build: compare it with the
`kacs/signing_keys` listing in securityfs, whose lines are in table order,
on a machine running that build. The same index on another build may be a
different key.

**Carried by:**

No event carries this field yet.

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
