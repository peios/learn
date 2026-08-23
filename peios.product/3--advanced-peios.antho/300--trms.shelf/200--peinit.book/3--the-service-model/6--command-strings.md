---
title: Command Strings
description: The four fields holding executable commands, how all four are parsed, how the executable is located, and ExecReload signals.
---

Four fields hold executable commands: `ExecStartPre`, `ExecStartPost`,
the command form of `ExecReload`, and `HealthCheck`. All four are parsed
the same way.

## Parsing

The string is split on whitespace into an argv, with double quotes
grouping. There is no shell — no expansion, no substitution, no
globbing, and peinit never invokes one. A command that needs shell
features is wrapped in a script.

Whitespace means exactly six characters: space, horizontal tab, line
feed, carriage return, form feed and vertical tab. Every other Unicode
whitespace code point is an ordinary argument character, which keeps the
split independent of the Unicode version peinit was built against.

Double quotes group text into one argv element and are not retained in
the result. Grouping may happen inside an argument, so
`--name="hello world"` becomes the single entry `--name=hello world`.
An empty quoted string is preserved as an empty argv entry.

Backslash has no escape semantics and is copied literally. A single
quote is an ordinary character.

An empty or whitespace-only command is invalid, and so is an unclosed
double quote.

## The executable

For all four fields, argv[0] is the executable path and begins with `/`.
Relative names, empty names and PATH-searched execution are decode
errors. Everything after argv[0] is an opaque string and is not path
validated.

## ExecReload signals

`ExecReload` may instead name a signal, as `signal:<NAME>`. The name is
an exact canonical Linux signal name. Numeric values, realtime signal
expressions, aliases, lowercase spellings and names with surrounding
whitespace are all invalid.

`SIGKILL` and `SIGSTOP` are invalid for reload, because a service cannot
handle either as a request to re-read its configuration.

The accepted set is the standard non-realtime Linux signals other than
those two:

`SIGHUP`, `SIGINT`, `SIGQUIT`, `SIGILL`, `SIGTRAP`, `SIGABRT`,
`SIGBUS`, `SIGFPE`, `SIGUSR1`, `SIGSEGV`, `SIGUSR2`, `SIGPIPE`,
`SIGALRM`, `SIGTERM`, `SIGSTKFLT`, `SIGCHLD`, `SIGCONT`, `SIGTSTP`,
`SIGTTIN`, `SIGTTOU`, `SIGURG`, `SIGXCPU`, `SIGXFSZ`, `SIGVTALRM`,
`SIGPROF`, `SIGWINCH`, `SIGIO`, `SIGPWR`, `SIGSYS`.

Names are validated when the definition is read and again before
delivery, and mapped to host signal numbers at that point. `ExecReload`
absent means SIGHUP.
