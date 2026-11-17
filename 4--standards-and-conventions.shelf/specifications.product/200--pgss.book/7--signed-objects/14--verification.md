---
title: Verification
description: What a verifier is given, the checks it makes in order, the
  seven results it can report, what it returns with each, and which
  results a consumer can rely on for what.
---

A verifier is given a file, or the content hash of one, and a bundle or
the means to find one (§7.9). It reports exactly one result.

## Results

The results are listed from least to most trusted.

| Result | Meaning |
|---|---|
| Unsigned | The file has no bundle |
| Invalid | An object is malformed, a signature or a link fails, the content hash does not match, a warrant is added or widened, or a limit is exceeded |
| Incomplete | A certificate the chain names could not be found (§7.11) |
| Refused | The chain is otherwise sound, and a member is revoked or distrusted |
| Consistent | The chain is sound, and its top-level is not enabled |
| Unrooted | The chain is sound, and its top-level is enabled but not vouched for by a root |
| Rooted | The chain is sound, and its top-level is enabled and signed by a root the verifier holds |

A verifier that cannot make a check at all, for want of memory or of an
algorithm, MUST report an error and MUST NOT report any of these
results. "Could not be checked" and "did not verify" are different
answers.

## The checks

A verifier MUST make these checks in this order, and reports the first
result that applies:

1. **Find the bundle.** If there is none, the result is Unsigned.
2. **Decode.** If the bundle or anything in it is malformed, or the
   bundle is over its size limit (§7.8), the result is Invalid.
3. **Check the content.** If the leaf's hash form is not the one the
   place calls for, or its content hash is not the file's (§7.9), the
   result is Invalid.
4. **Complete the chain.** Find each certificate the bundle names and
   does not carry (§7.11). If one is not found, the result is
   Incomplete. If the chain holds more than 16 intermediaries, the
   result is Invalid.
5. **Check the links.** Every `issuer` names the next member, every
   signature verifies, and only the last certificate is a top-level
   (§7.3, §7.6). A top-level whose issuer is a key the verifier does not
   hold has no signature the verifier can check, and passes this step
   unchecked. Any failure makes the result Invalid.
6. **Check the warrants.** Every child narrows against its parent, each
   certificate that issued a certificate holds `Delegate`, the leaf's
   name is within its issuer's `Name`, and the leaf holds none of the
   three warrants it is forbidden (§7.5). An unrecognized warrant with
   Must Understand set, anywhere in the chain, fails this step. Any
   failure makes the result Invalid.
7. **Apply revocations and distrust.** If a revocation applies to the
   chain (§7.12), or a member is distrusted (§7.13), the result is
   Refused.
8. **Place the top-level.** If the top-level is not enabled (§7.10), the
   result is Consistent. If it is enabled and step 5 verified its
   signature under a root, the result is Rooted. Otherwise the result is
   Unrooted.

A verifier applies no clock at any step. No object holds a time, and a
chain that verifies once verifies until it is revoked or distrusted.

## What a verifier returns

With Consistent, Unrooted, and Rooted, a verifier MUST return:

- the leaf's name
- the leaf's warrants
- the object hash of the chain's top-level
- for Rooted, the key hash of the root

With Refused, a verifier MUST say whether the cause was a revocation or
a distrust entry. With any other result it returns nothing about the
chain.

The leaf's warrants are the chain's effective warrants. Step 6 has
already bounded them by every certificate above the leaf, so a consumer
needs nothing else from the chain, and MUST NOT decode the bundle to
reach a decision of its own.

## What each result is good for

**Rooted** is the strongest statement a system can make about a file:
a root the verifier was built with vouches for the top-level's
warrants, and the system has that top-level enabled. A consumer that
grants anything an administrator could not grant MUST require it.

**Unrooted** says the system's administrator trusts the top-level, and
nothing more. The top-level's warrants are whatever its maker wrote. A
consumer MAY accept Unrooted for a decision that is the administrator's
to make, and SHOULD compare the returned top-level hash with the one it
expects where it expects a particular one.

**Consistent** says only that the chain agrees with itself. Anyone can
make such a chain. A consumer MUST NOT accept it unless it keeps its
own list of top-levels and finds the returned hash there.

**Refused**, **Incomplete**, **Invalid**, and **Unsigned** confer
nothing. A consumer MUST NOT treat Invalid as it treats Unsigned where
the difference matters to it: a file with no bundle made no claim, and a
file with a bad one made a claim that failed.

> [!NOTE]
> Invalid is not always tampering. A verifier that meets a warrant it
> does not recognize, with Must Understand set, reports Invalid for a
> chain a later verifier would accept. The guidance is the same either
> way, and a system that reports the cause to its administrator SHOULD
> distinguish the two.
