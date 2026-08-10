---
title: Repositories and trust
type: concept
description: A repository is an HTTP location that serves signed packages. This page covers the repo commands, the trust ceremony that anchors a repository to a signing key, how key rotation propagates, what signature policy and priority control, and the freshness protection that stops a stale repository being passed off as current.
related:
  - peios/package-management/overview
  - peios/package-management/installing-and-removing
  - peios/package-management/keeping-a-system-current
  - peios/package-management/dependency-resolution
---

A **repository** is where packages come from: an HTTP or HTTPS location that serves `.peipkg` files alongside signed indexes describing them. A Peios system has zero or more repositories configured, and the `peipkg repo` commands manage that configuration.

Beyond configuration, this page covers **trust**: establishing that the packages a repository serves are genuinely the ones its operator published, and not something a network attacker or a compromised mirror substituted.

## What a repository serves

At its base URL a repository serves three signed documents:

- A **descriptor** — the repository's identity: the set of signing keys it uses, each with a status. This is the root of trust for everything else.
- An **active index** — the catalogue of current package versions: names, versions, dependencies, hashes, and download locations.
- An **archive index** — the catalogue of older versions, kept so a [downgrade](~peios/package-management/keeping-a-system-current) can reach them. peipkg fetches it only on demand.

The descriptor and the indexes each carry a detached signature. peipkg verifies all of them; an unverifiable document is discarded, never used.

## Adding a repository

```
peipkg repo add <name> <base-url> --anchor <fingerprint>
```

`repo add` does two things: it records the repository in your configuration, and it runs the **trust ceremony** that anchors it.

```
$ peipkg repo add official https://pkgs.peios.org \
    --anchor ef86709c4b1d8a02e5f3c719d640aa8b7c2e9105f8d3b6470a1c2e9d8b5f3a04
added repository "official"
```

The `--anchor` value is a **signing-key fingerprint**, and it is the part of the command that establishes trust. peipkg cannot tell you whether a repository is genuine; only you can, by obtaining its fingerprint through a channel you trust (the project's website over HTTPS, a colleague, a printed reference) and supplying it here. The anchor is your out-of-band statement that the key is trusted.

Given an anchor, the ceremony runs:

1. peipkg fetches the repository's descriptor and its signing keys.
2. It checks the fetched keys against the anchors you supplied — a fingerprint must match bit for bit.
3. Only if the descriptor's signature verifies against an anchored key does peipkg accept it and record the trust state.

If the fetched descriptor does not verify against any anchor, `repo add` fails and leaves nothing behind — no half-added repository, no configuration file. You can supply `--anchor` more than once to trust several keys at first contact.

| Option | Default | Effect |
|---|---|---|
| `--anchor FINGERPRINT` | — | A signing-key fingerprint to trust. Repeatable. |
| `--priority N` | `50` | Resolution priority — a lower number wins. See below. |
| `--policy required\|optional` | `required` | Whether a valid signature is required. See *Signature policy*. |
| `--min-index-version N` | `0` | A freshness floor for the index. See *Freshness*. |
| `--max-trusted-age-days N` | `30` | How stale the repository's trust state may grow before operations force a refresh. See *Freshness*. |
| `--insecure` | off | Permit a plain `http://` base URL. |

`--insecure` exists for a repository on a trusted local network with no TLS. It lowers transport confidentiality and integrity; the package signatures still protect authenticity, but prefer `https://` whenever it is available.

## How trust survives key rotation

A repository operator will, over time, rotate signing keys — retiring an old one, bringing a new one into use. If trust were pinned permanently to the fingerprint you first anchored, every rotation would break every consumer.

Rotation does not break trust, because the descriptor carries the keys. Each key in the descriptor has a status:

| Status | Meaning |
|---|---|
| `active` | In current use for signing. |
| `transitioning` | Being phased in or out — honoured until its stated expiry. |
| `revoked` | Withdrawn — never honoured again. |

Each time peipkg refreshes a repository, it verifies the new descriptor against the keys in the descriptor it already trusts, and then adopts the new descriptor's key set as the current trust state. A rotation that is itself signed by a still-trusted key propagates automatically: you anchored once, and the chain carries forward from there without you re-anchoring. A `revoked` key is dropped and never accepted again.

The anchor therefore matters only at first contact. After that, trust is a chain, and each refresh extends it.

## Signature policy

`--policy` chooses how strict peipkg is about signatures for this repository.

- **`required`** (the default) — every descriptor and index must carry a valid signature from a trusted key. An unverifiable document is rejected. This is the correct setting for any repository reached over a network.
- **`optional`** — combined with no trust anchors, this puts the repository into **unsigned mode**: peipkg fetches and uses its metadata and packages without cryptographic verification.

Unsigned mode is a deliberate escape hatch for a scratch repository on a build host, or a local mirror you fully control. Every operation that touches an unsigned repository prints a warning:

```
peipkg: warning: repository "scratch" is unsigned — its metadata and
packages are not cryptographically verified
```

In unsigned mode, only the transport stands between you and a substituted package. Do not use it for anything reachable from an untrusted network.

## Priority

`--priority` is a number — lower is stronger, default `50` — that decides which repository wins when **more than one offers the same package**. If both an `official` repository at priority `10` and an `internal` one at priority `20` carry `nginx`, the resolver takes the `official` build. Priority does not restrict anything; it only breaks ties. Its full role in version selection is covered in [Dependency resolution](~peios/package-management/dependency-resolution).

Priority also feeds one of the safety checks there: a package from a *lower*-priority repository that tries to displace a package installed from a *higher*-priority one is flagged for explicit authorisation, so a low-trust repository cannot quietly take over a package you got from a trusted one.

## Freshness — defeating a stale-repository attack

A signature proves a document is authentic; it does not prove the document is current. An attacker who cannot forge a signature can still serve you a genuine, correctly-signed, but old index — one from before a security fix was published — and a naive consumer would accept it.

peipkg closes that gap by tracking, per repository, the highest index version it has ever seen, and refusing any index that goes backward. Once you have seen version 5 of an index, version 4 — however well signed — is rejected. A repository can only ever move forward.

`--min-index-version N` lets you set that floor explicitly, out of band: if you know the current index is at least version `N`, anchoring that number means peipkg will reject anything older even on the very first fetch, before it has a history to compare against.

Going backward is one half of the attack; standing still is the other. A frozen repository — one that serves the same, correctly-signed index forever — never trips the rollback check, yet it can hold you on a view from before a security fix indefinitely. Against that, peipkg tracks when each repository last refreshed **with progress** and enforces a **maximum trusted age**: 30 days by default, tunable per repository with `max_trusted_age_days` in its `.repo` file or `--max-trusted-age-days` at add time.

When an install, upgrade, or downgrade finds a repository's trust state older than its maximum, peipkg refreshes that repository first. If it cannot — the repository is unreachable, or it refreshes without progressing — the operation is refused rather than planned against outdated metadata. Passing `--allow-stale` to the operation overrides the refusal; the override is warned about and recorded in the audit stream. A maximum above 180 days draws a warning on every operation, because a bound that loose effectively disables the check.

## Listing and removing repositories

```
peipkg repo list
peipkg repo remove <name>
```

`repo list` prints the configured repositories — name, base URL, priority, signature policy. It accepts `--json`.

```
$ peipkg repo list
official  https://pkgs.peios.org  priority=10  required
internal  https://pkg.corp.example  priority=20  required
```

`repo remove` deletes a repository's configuration and the trust state peipkg recorded for it. Packages already installed from that repository stay installed — removing a repository controls where future packages come from; it does not remove past ones. Those packages simply no longer have a source for upgrades until you add a repository that carries them again.

## Where the configuration lives

Each repository is one file: `/conf/peipkg/<name>.repo`, in flat TOML.

```toml
base_url         = "https://pkgs.peios.org"
priority         = 10
signature_policy = "required"
trust_anchors    = ["ef86709c4b1d8a02e5f3c719d640aa8b7c2e9105f8d3b6470a1c2e9d8b5f3a04"]
```

The files are hand-editable, and editing one is a legitimate way to configure a repository — a trust anchor written into the file is you supplying that anchor out of band. `peipkg repo add` is the convenient front end: it runs the ceremony and writes the file for you. Who may edit these files is, like everything else on Peios, the [security descriptor](~peios/security-descriptors/overview) on `/conf/peipkg/`.

## Exit status

| Code | Meaning |
|---|---|
| `0` | The operation succeeded — the repository was added, listed, or removed. |
| `1` | The operation failed — the trust ceremony failed (`repo add` backs out and leaves nothing behind), or the subcommand was missing, unknown, or given the wrong arguments (a missing `repo add <name> <base-url>`, a malformed option). Removing a name that is not configured is not a failure. |
| `2` | A usage error before any command ran — no command, an unknown command, or a malformed global option. |
