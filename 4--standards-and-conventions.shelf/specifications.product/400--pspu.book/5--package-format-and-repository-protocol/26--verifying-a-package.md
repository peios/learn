---
title: Verifying a Package
description: What a consumer checks before it stores a package, the order of the checks, and what they prove and don't.
---

A consumer copying a package from one artifact directory to another trusts
nothing it reads from the source. Before it stores the package, it MUST
check, in this order:

1. **The ref** holds exactly one identity and a newline (§5.11).
2. **The manifest** hashes to that identity, is in the one form §5.18
   gives, names the package ID asked for, and holds only paths that meet
   §5.13.
3. **Each blob** copied hashes to the name the manifest gives it (§5.12).

From a repository served over HTTP, the identity is the one its catalog
gives, and there is no ref to check (§5.34).

A stored file takes only its content from the source: it is given the
security metadata its entry records (§5.20, §5.16).

If a check fails, the consumer MUST stop without writing the manifest or the
ref. Blobs copied before the failure are named by their content, and MAY be
kept. Only a package whose manifest and ref are written is stored.

## Already present

If the package is already stored with the same identity, the consumer copies
only the blobs that are missing. If it is stored with another identity, the
consumer MUST refuse it (§5.11).

## What this proves

These checks prove that the package is the one the source's ref names. They
don't prove who published it. A package fetched through a machine's
configuration of a repository that gives a key is proved published by it
too: it MUST be in the catalog that the signed pointer file leads to, at the
identity the catalog gives (§5.29, §5.33). A package fetched from a
directory named directly is not.
