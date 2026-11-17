---
title: Terminology
description: The terms this chapter is specified in, covering object, root,
  top-level, intermediary, leaf, bundle, warrant, trust store, revocation,
  distrust, and quarantine.
---

**Object.** One of the encoded structures of this chapter: a certificate,
a leaf, a bundle, a revocation, or a distrust entry. Every object begins
with the header of §7.4.

**Root.** A public key a verifier is built with. A root has no
certificate and holds no warrants. It signs top-level certificates and
nothing else.

**Certificate.** An object that binds a public key to a name and a set of
warrants, signed by its issuer (§7.6). A certificate is a **top-level**
or an **intermediary**.

**Top-level.** A certificate at the head of a chain. A root signs it, or
it signs itself.

**Intermediary.** A certificate issued by a top-level or by another
intermediary.

**Leaf.** A signed statement that a file has a given content hash, made
under a name and requesting a set of warrants (§7.7). A leaf holds no
key, so nothing can be issued beneath it.

**Chain.** A leaf, the certificate that issued it, and each issuer in
turn up to a top-level.

**Bundle.** The object a file carries: a leaf and as much of its chain
as the signer chose to include (§7.8).

**Warrant.** A named power written into a certificate or requested by a
leaf (§7.5). A power that is not written down is not held.

**Trust store.** The directories that say which top-levels a system
trusts, which revocations it applies, and what its administrator
distrusts (§7.10).

**Enabled.** Said of a top-level the trust store accepts (§7.10).

**Quarantined.** Said of a self-signed top-level that a package ships
and the administrator has not approved (§7.10).

**Revocation.** A signed object by which an authority withdraws a
certificate or a leaf beneath it (§7.12).

**Distrust.** An unsigned entry by which a system's administrator
refuses a certificate or a leaf on that system (§7.13).

**Object hash.** The SHA-512 hash of all of an object's bytes, its
signature included (§7.4).

**Key hash.** The SHA-512 hash of a key type byte followed by the key it
describes (§7.4).

Terms defined in PSPU §5.2 (package and closure) are used with the same
meaning and are not redefined. *Extended attribute* is used as the Peios
Kernel TRM defines it.
