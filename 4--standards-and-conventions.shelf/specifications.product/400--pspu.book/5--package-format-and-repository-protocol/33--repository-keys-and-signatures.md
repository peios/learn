---
title: Repository Keys and Signatures
description: How a repository's pointer file is signed with a PSO bundle, the Repository warrant, the identity a repository signs as, what a machine requires of the result, and what a signature vouches for.
---

A repository is signed as PGSS Signed Objects defines (PGSS §7).
Publishing a repository MUST sign its pointer file.

## The signature

`repository.pso` is a detached bundle (PGSS §7.9) over the pointer file's
bytes. Its leaf:

- has the whole-file hash form;
- is issued under the repository's **identity**, a name in the form of
  PGSS §7.7, such as `pkgs.peios.org`;
- holds the `Repository` warrant.

A publisher SHOULD publish a bundle that carries every intermediary of its
chain. A machine reading a repository for the first time has none of the
publisher's packages, and so none of the intermediaries they would install.

A publisher MUST check the signature it made before writing it.

## The warrant a signer needs

`Repository` is a warrant in the sense of PGSS §7.5.

| Name | Type | Allow Equal | `flags` | Meaning |
|---|---|---|---|---|
| `Repository` | Set, empty | Set | `0x80` | The holder can sign a repository's pointer file |

The warrant carries no value. Which repository a leaf signs for is the
leaf's name, which the chain already bounds through the `Name` warrant
(PGSS §7.5).

> [!NOTE]
> The warrant separates signing a repository from signing anything else.
> A certificate issued to sign programs can't sign a pointer file unless
> its issuer gave it `Repository` as well, so a key taken from a build
> machine doesn't hand over the repository with it.

## Keys

A publisher's keys and certificates are an authority's (PGSS §7.1), and
are issued and kept as that chapter says. A private key MUST NOT be kept
in the repository, or anywhere it is published.

A publisher replaces its signing certificate without any machine's
configuration changing: a machine names the repository's identity
(§5.35), not a key.

## What a machine requires

A machine checks a repository's signature only if its configuration of the
repository gives an identity (§5.35), and only when it fetches through that
configuration. It verifies `repository.pso` against the pointer file (PGSS
§7.14) and MUST refuse the repository unless all of these hold:

- the result is Rooted, or is Unrooted and the configuration says
  `unrooted = true`;
- the leaf holds `Repository`;
- the leaf's name is the configured identity, byte for byte;
- if the configuration gives an anchor, the chain's top-level is the one
  it names.

A consumer MUST NOT accept a Consistent result, whatever the configuration
says.

> [!NOTE]
> Rooted is the default so that the configuration a system ships for its
> own repository can't be satisfied by a top-level an administrator
> enabled for something else. An Unrooted top-level is trusted for the
> names its `Name` warrant states, which the administrator saw when
> enabling it (PGSS §7.10), so a repository that opts in needs no pin. An
> anchor is a second line of defense against a top-level enabled with a
> wider `Name` than a repository's operator expected.

## What it vouches for

When the signature is accepted, a package is taken from the repository
only if the catalog the pointer file names lists it, at the identity the
catalog gives (§5.29). Every tree node, manifest and blob is reached
through hashes from the pointer file, so for a repository used that way the
signature vouches for all of them.

Reading the same directory as a plain artifact directory, without its
configuration, checks none of this: its refs are taken as they are (§5.26).

A repository without an identity in the machine's configuration, such as a
medium's store or a local directory, is trusted because whoever configured
it supplied it. A repository served over HTTP without one is trusted for
whatever its server sends, so a machine's configuration of one SHOULD give
its identity.
