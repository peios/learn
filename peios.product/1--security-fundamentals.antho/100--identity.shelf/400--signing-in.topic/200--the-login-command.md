---
title: The login command
type: reference
description: login is the terminal client for PGSS Logon — it collects an identifier and whatever credentials the authority asks for, and starts your shell.
related:
  - peios/signing-in/overview
  - peios/logon-sessions/overview
  - peios/managing-local-principals/creating-accounts
  - peios/managing-local-principals/lps-command
  - peios/services-and-jobs/controlling-services
---

`login` is the terminal client for [signing in](~peios/signing-in/overview). It collects an identifier, renders whatever credential prompts the authority sends, installs the token it is granted, and replaces itself with your shell.

```
login [name] [options]
login --try <name> [options]
login --try-no-password <name> [options]
```

It does not know what a password is. It renders the prompts it is asked to render and returns the answers, so adding a new credential type — a one-time code, a smartcard — changes the authority and leaves `login` alone.

## Naming a principal, or not

With no name, `login` asks for one:

```
Username: alice
Logging in as alice
Password:
```

With a name, the first prompt is skipped. The `Logging in as` line comes from the authority rather than from `login`, so it will gain a realm once authorities have them.

A principal who needs no credential is signed in immediately, with no prompt at all — see [passwordless accounts](~peios/managing-local-principals/creating-accounts).

## `--try` and `--try-no-password`

Both attempt a named principal and fall back to an ordinary prompt rather than failing. They differ in what they offer to collect.

**`--try <name>`** attempts the principal with `login`'s full capabilities. A passwordless principal is signed in immediately; one with a password is prompted for it.

**`--try-no-password <name>`** attempts the principal while declaring that it can collect nothing, so only a principal who needs no credential can succeed. This is what a console autologon uses.

Neither flag asserts that anyone is authenticated. The authority still decides, and understating what you can collect only denies you prompts you could have rendered — so running either by hand gains you nothing you did not already have.

| | Passwordless | Has a password | No such principal |
|---|---|---|---|
| `login alice` | signed in | prompts | `user alice does not exist` |
| `login --try alice` | signed in | prompts, then falls back if wrong | falls back silently |
| `login --try-no-password alice` | signed in | falls back silently | falls back silently |

A fallback restarts the sign-in from `Username:`, so you are never locked to the principal that was attempted.

### When a fallback explains itself

`login` says why it fell back only if something was already on your terminal.

A `--try` that reached a password prompt has interrupted you, and dropping to `Username:` without a word would read as a fault — you typed a password and got asked for a name. So it reports first:

```
$ login --try alice
Logging in as alice
Password:
login: Password incorrect
Username:
```

A `--try-no-password` that was refused before anything was rendered has interrupted nobody, and stays quiet. That is what keeps a line about a failed autologon off the console of every machine where the principal simply has a password.

Falling back is limited to denials another principal could survive. A failure of the authority itself is reported and `login` exits, because offering a prompt that cannot work either would spin a console.

### Where existence is checked

`login` asks `/run/ident.sock` whether a principal exists, not the logon socket. The logon socket will not tell it — an authority never distinguishes an unknown principal from a bad credential — while the identity socket answers plainly, which is what it is for.

If that lookup cannot be answered, `login` attempts the sign-in anyway rather than reporting an absence. An unreachable source reported as "no such user" would turn an outage into a fact.

## Autologon on a console

A console that signs in on its own is a passwordless principal plus `--try-no-password`. On a live image, `peinit` starts:

```
/bin/login --try-no-password peios
```

The same service definition suits an image where `peios` has a password: the attempt is refused before anything is rendered, and an ordinary prompt appears. No second seed, and no conditional configuration.

To turn autologon off, give the principal a password with [`lps password`](~peios/managing-local-principals/lps-command). To move the prompt to another terminal, change the service's `TTYPath` — see [controlling services](~peios/services-and-jobs/controlling-services).

## Options

| Option | Effect |
|---|---|
| `--try <name>` | Attempt `name`, falling back to a full prompt. |
| `--try-no-password <name>` | Attempt `name` collecting nothing, falling back to a full prompt. |
| `-p` | Keep the inherited environment instead of building a fresh one. |
| `-h <host>` | Record the remote peer for a sign-in originated on its behalf. Unverified. |
| `-H` | Accepted and ignored. Suppresses the hostname banner on other systems. |
| `--` | Treat everything after as a name, not an option. |

`-f` is **not** implemented. On Linux it means "trust me, they are already authenticated", gated only by the caller being root. On Peios that decision belongs to the authority, taken from the verified peer, so accepting a flag here would put an authentication bypass in an unprivileged process.

## The environment your shell starts in

Without `-p`, `login` builds a fresh environment: `HOME`, `SHELL`, `USER`, `LOGNAME`, `PATH=/bin`, and `TERM` carried through from its own. The shell's `argv[0]` gets a leading dash, which every shell reads as "this is a login shell, run the profile files".

The home directory comes from the profile the authority sent, and **a missing one is not fatal**. `login` reports it and starts you in `/`. Refusing to proceed over an absent directory would turn a cosmetic problem into being locked out, and creating it would put directory provisioning inside the one program that has to keep working when everything else is broken.

## Exit status

`login` does not return on success — it replaces itself with your shell, so what you see afterwards is the shell's exit status.

| Code | Meaning |
|---|---|
| `1` | A usage error, a denied sign-in, or the shell could not be started. |
