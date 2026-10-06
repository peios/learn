---
title: Quick start
type: how-to
description: Build clackatoo, start the daemon, and drive a shell from the command line by starting a terminal, typing into it, reading its screen and closing it.
related:
  - clackatoo/getting-started/what-is-clackatoo
  - clackatoo/reference/cli
---

## Build it

clackatoo is a Cargo workspace. Build the `clackatoo` command in release mode:

```sh
cargo build --release -p clackatoo
```

The binary is `target/release/clackatoo`.

## Start the daemon

```sh
clackatoo daemon
```

The daemon runs in the foreground and logs to stderr. Set `RUST_LOG=debug` for more detail. Only one daemon runs per user: a second one refuses to start. Stopping the daemon (Ctrl-C) hangs up every terminal it owns.

## Drive a terminal

From another terminal, start one. `new` prints the new terminal's ID:

```sh
$ clackatoo new
1
```

It runs your `$SHELL` in the current directory, at 80×24. Type a command into it and press Enter with `run`:

```sh
clackatoo run 1 ls --color=always
```

See what it shows with `capture`. Add `--ansi` to keep the colours:

```sh
clackatoo capture 1 --ansi
```

`send` types text without pressing Enter, which is how you drive full-screen programs:

```sh
clackatoo run 1 htop
clackatoo send 1 q
```

List terminals, and close one when you're done:

```sh
clackatoo list
clackatoo close 1
```

Closing a terminal hangs up its program, as closing a terminal window would. A terminal whose program exits stays listed, with its exit status and last screen, until you close it.
