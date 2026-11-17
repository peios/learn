---
title: Scope and Roles
description: What PGSS Signed Objects specifies, a certificate chain with
  warrants that vouches for a file's bytes, and the four roles that issue,
  keep, verify, and rely on it.
---

This chapter specifies the **Peios Signed Object (PSO)**: a way for a
party to vouch for the bytes of a file, and for a system to decide how
far that statement is trusted.

A PSO is not a bare signature. It is a chain of certificates ending in a
signed statement about one file, and every power the chain confers is
written into it as a warrant (§7.5). A verifier walks the chain, checks
that no certificate claims more than the one that issued it, and reports
which of the system's trust anchors the chain ends at.

Four roles participate.

| Role | Obligation |
|---|---|
| Authority | Holds a key and a certificate for it. Issues certificates, leaves, and revocations, and every rule on what those objects contain binds the authority. |
| Store keeper | Maintains the system's trust store (§7.10): which top-level certificates are trusted, which revocations apply, and what the administrator distrusts. |
| Verifier | Validates a bundle against a file and the trust store, and reports a result (§7.14). Every validation and rejection rule binds the verifier. |
| Consumer | Asks a verifier about a file and acts on the result. A consumer decides which results and which warrants it accepts. |

The authority and consumer roles are publicly implementable. A third
party MAY issue its own certificates and leaves, and MAY write a consumer
that gives its own meaning to a warrant, and interoperate with the rest
unchanged. A system has one store keeper and at least one verifier, and a
system with several verifiers MUST have them agree: two verifiers on one
system, given the same bundle, file, and store, return the same result.

This chapter covers:

- the chain and what each part of it is (§7.3)
- the encoding shared by every object, and the hash and signature
  algorithms (§7.4)
- warrants: their encoding, how they narrow, and the three this chapter
  defines (§7.5)
- certificates, leaves, and bundles (§7.6, §7.7, §7.8)
- where a bundle is carried and which bytes of the file it covers (§7.9)
- the trust store, and how a certificate that is not carried is found
  (§7.10, §7.11)
- revocation and distrust (§7.12, §7.13)
- verification and its results (§7.14)

This chapter does not cover:

- What any warrant other than `Delegate`, `Revoke`, and `Name` means.
  The specification of the consumer that acts on a warrant defines it.
- What a consumer does with a result: whether a program runs, at what
  protection, or whether a repository is believed. For executables on
  Peios that is PSPK §3.
- How a verifier inside a kernel is given the trust store, and the
  interface through which a store keeper changes it while the system
  runs. For the Peios kernel that is PSPK §6.
- How an administrator's approval is obtained. This chapter requires
  that it is (§7.10), and the store keeper's documentation says how.
- Key generation, custody, and rotation. Those are the authority's.
- Certificates for network protocols. Those are X.509 (RFC 5280) and are
  unrelated to this chapter.
