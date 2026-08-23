---
title: Decompression Bounds
description: The two bounds every consumer enforces against extreme compression ratios, checked continuously, and what happens when one is exceeded.
---

A consumer MUST bound package decompression, to prevent
resource-exhaustion attacks by packages with extreme compression ratios.

Two bounds apply, and both MUST be enforced.

## The index-declared bound

The repository index entry's `size_compressed` and `size_installed`
fields (§5.33) bound the legitimate sizes of the compressed and
uncompressed forms. During streaming decompression a consumer MUST
verify that:

- the cumulative compressed bytes consumed do not exceed
  `size_compressed` by more than **the lesser of 1% or 16 MiB**; and
- the cumulative decompressed bytes produced do not exceed
  `size_installed` plus a fixed overhead allowance of **320 MiB**.

Both figures MUST be taken from the **index entry**, not from the
package's own manifest. The manifest lives inside the compressed stream
and is therefore under the control of whoever produced the bytes being
bounded.

> [!NOTE]
> This is the whole point of the bound, and it is easy to get backwards.
> A consumer that reads `size_installed` out of the manifest it is in
> the middle of decompressing has derived its cap from the input it is
> defending against: a hostile package simply declares a large enough
> figure. The index entry is signed by the repository, independently of
> the package, which is what makes it usable as a bound.

The 320 MiB decompressed allowance bounds the structural overhead a
conforming package may legitimately carry above its installed payload:
tar headers and block padding for up to the §5.A limit of 100,000
entries, plus the metadata files at their maximum sizes. A typical
package's overhead is a tiny fraction of it; the allowance is sized so
that a consumer never rejects a package conforming to §5.A.

## The absolute cap

Independently of any declared size, a consumer MUST abort decompression
when the cumulative decompressed output exceeds an absolute cap. The
default cap is **4 GiB**. A consumer MAY raise it through operator
configuration but MUST NOT raise it silently.

## Checked continuously

Both bounds MUST be checked on **every chunk** of output, not at
end-of-stream.

> [!NOTE]
> Constructed Zstandard payloads can achieve compression ratios beyond
> 10,000:1, so a 10 MB package can decompress to terabytes. A check
> deferred to end-of-stream never runs.

## On exceeding a bound

Exceeding either bound MUST cause the package to be rejected with no
further processing and nothing committed to disk.

## Cross-checking the declared size

The manifest's `size_installed` and the index entry's `size_installed`
MUST be equal, and a consumer MUST verify that equality (§5.32).
Together with the files-manifest sum required by §5.18, this makes the
figure a quantity all three of the producer, the repository, and the
consumer can compute independently and agree on.
