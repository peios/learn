---
title: Claims
type: reference
description: A claim is a shared filesystem name that only one installed package may hold. How claims materialise as symlinks, and the claim command for reassigning them.
related:
  - peios/package-management/overview
  - peios/package-management/dependency-resolution
  - peios/package-management/installing-and-removing
---

Some filesystem names can be provided by more than one package. Two registry daemons — `loregd` and an alternative — both install a working binary, but only one of them can own `/usr/bin/registryd`. peipkg calls that shared name a **claim**, and it owns the machinery that decides which package holds it.

Three words are used precisely on this page:

- A **claim** is a single shared filesystem name that many installed packages may be able to answer, but exactly one may hold at a time.
- An **eligible provider** is an installed package able to answer a given claim.
- The **holder** is the one package that currently answers it.

(This is unrelated to [token claims](~peios/identity/claims) — the security-token attribute concept in the identity docs. The same word names a different subsystem.)

## What a claim is

A claim materialises as a **symlink** on disk. The link lives at the **claim path** — the shared name, such as `/usr/bin/registryd` — and points at a file inside the holder's payload, the **target**, such as `/usr/sbin/loregd`. Ask the system for the shared name and you reach whichever provider currently holds it.

```
/usr/bin/registryd -> /usr/sbin/loregd
```

The claim symlink is **owned and managed by peipkg**. It is not shipped inside any package's payload; no provider installs it, and removing a provider does not remove it out from under peipkg. peipkg creates, repoints, and tears down the link as part of the transactions that install, remove, grant, and revoke.

The two sides of a claim are declared in package manifests:

- A **provider** package declares the **target** file it offers for a claim — the real binary the shared name would resolve to.
- A **consumer** package references the **claim path** where it expects the shared name to appear.

peipkg joins the two. A provider can offer a target for a claim, a consumer can depend on the name being present, and peipkg mediates between them, keeping exactly one provider wired to the shared path at any moment.

## Claims and provides/replaces

A claim is the "exactly one owner of a shared name" extension of the `provides` and `replaces` relationships covered in [Dependency resolution](~peios/package-management/dependency-resolution). There, several packages can advertise the same *virtual* name and any one of them satisfies a dependency written against it — that mechanism answers "is something here that provides this?". A claim goes one step further: it answers "which single provider owns this concrete filesystem name right now?", and enforces that the answer is never more than one. Provides establishes that a name can be answered; a claim decides which package answers it on disk.

## Auto-claim on install

Installing an eligible provider auto-claims every claim it provides that is currently unheld. If no package yet holds `registryd`, installing `loregd` makes `loregd` the holder and materialises the link as part of the same transaction — you get a working shared name without a second step.

The rule is strictly unheld-only. Auto-claim never overrides a claim that is already held by another package. Install a second registry daemon while `loregd` holds `registryd` and the newcomer is installed as an eligible provider but takes nothing; `loregd` stays the holder. Reassigning a held claim is always a deliberate act — see the `claim` command below, or the install flags that force it.

### Install flags

`peipkg install` accepts flags that override the default auto-claim behaviour for the packages in that install:

| Option | Effect |
|---|---|
| `--no-claim` | Claim nothing. Install the provider(s) without taking any claim, even ones that are currently unheld. |
| `--claim <names>` | Force-claim the named claims (comma-separated), overriding the current holder of each. |
| `--claim-all` | Force-claim every claim the installed packages provide, overriding incumbents. |

Two combinations are hard errors:

- `--claim-all` together with `--claim`.
- `--claim-all` together with `--no-claim`.

`--claim` and `--claim-all` are how you take a claim that is already held during an install; without them, an install only ever fills claims that are empty.

## The claim command

`peipkg claim` inspects a claim and reassigns its holder. It has three forms.

```
peipkg claim <claim>
peipkg claim <claim> grant <package>
peipkg claim <claim> revoke
```

**Report status.** With just a claim name, peipkg prints the current state of the claim: the current holder, the materialised links shown as `path -> target`, and the installed eligible providers.

```
$ peipkg claim registryd
holder: loregd
links:
  /usr/bin/registryd -> /usr/sbin/loregd
eligible providers:
  loregd
  altregd
```

**Grant.** `grant <package>` makes an installed eligible provider the holder. peipkg atomically repoints all of the claim's links to that package's targets — every path the claim covers moves together, or none does. The named package must be an installed eligible provider for the claim.

```
$ peipkg claim registryd grant altregd
```

**Revoke.** `revoke` removes the grant. The claim becomes **unheld** and its links are torn down. peipkg does not automatically promote another provider — a revoked claim has no holder until you grant one.

| Option | Effect |
|---|---|
| `--yes`, `-y` | Skip the confirmation prompt. Applies to `grant` and `revoke`. |

`grant` and `revoke` each run as a standalone transaction. Like every other peipkg change they appear in [`history`](~peios/package-management/transactions-and-recovery), can be reversed with [`undo`](~peios/package-management/keeping-a-system-current), and are fully auditable — each emits a `claim` event to the [audit stream](~peios/auditing/overview). A reassignment is never a silent, unrecorded edit to a symlink; it is a first-class, reversible operation.

## What happens on uninstall

Uninstalling the current holder **auto-withdraws** the claim. The holder is going away, so peipkg tears down its links and the claim becomes **unheld** as part of the removal.

peipkg does not auto-promote another provider in its place — an automatic promotion would be the kind of silent reassignment claims exist to prevent. Instead it surfaces the remaining eligible providers and hands you a ready-to-run command to reassign the claim yourself:

```
$ peipkg remove loregd
...
claim 'registryd' is now unheld. eligible providers: altregd
to reassign it, run:
  peipkg claim registryd grant altregd
```

If the holder was the only eligible provider, the claim is left unheld with nothing to promote, and any consumer relying on the shared name will find it absent until a new provider is installed.

## Exit status

| Code | Meaning |
|---|---|
| `0` | The operation succeeded — the status was reported, or the grant or revoke was applied (a declined prompt is also `0`: nothing failed). |
| `1` | The operation failed — the claim has no eligible provider, the named package is not an eligible provider, or a named package or claim is not installed. |
| `2` | A usage error — an unknown subcommand (the only subcommands accepted after the claim name are `grant` and `revoke`) or a malformed option. |
