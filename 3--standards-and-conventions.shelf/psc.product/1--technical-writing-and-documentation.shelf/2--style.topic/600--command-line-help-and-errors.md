---
title: Command-Line Help and Errors
type: reference
description: How first-party Peios programs print help, version, and error
  messages, covering the help layout, option descriptions, placeholders, the
  required flags, output streams, exit statuses, and the form of an error
  message.
---

Every first-party Peios program, from a command a user runs to a daemon,
prints help, its version, and error messages in the same way. Help is the
shortest form of Peios documentation: a reminder of what a program accepts,
printed by the program itself. [Core Style](~psc/core-style) applies to its
wording; this page adds the layout and the rules for output and exit
statuses.

These rules cover what a program writes to a terminal. Messages a daemon
logs are events, which evman documents, and this page doesn't cover them.

## Help summarizes the man page

The man page is the authority for a program's interface; help is a summary
of it. Help lists every command, argument, and option, with one line each,
and leaves explanation, examples, and edge cases to the man page.

Help and the man page must never disagree. Change both in the same commit.

Where the argument parser can generate help from its own definitions, as
clap can, let it. A program that writes its help by hand keeps one copy of
the text and builds any other usage message from it, so the two can't drift
apart.

## Layout

Help has these parts, in this order, separated by blank lines:

1. **Description.** One line: the description from the man page's NAME
   line, with its first letter capitalized and no final period.
2. **Usage.** `Usage:` followed by the program's invocation forms.
3. **Commands, arguments, and options.** One section each, for those that
   apply, headed `Commands:`, `Arguments:`, and `Options:`.
4. **Pointer.** One line saying where the full documentation is.

The help for a print spooler's control program looks like this:

```text
Inspect and control the Exampled print spooler

Usage: spoolctl [options] <command>

Commands:
  status            Show the spooler's state and queue length
  pause             Stop accepting new jobs
  resume            Start accepting jobs again
  cancel <job-id>   Cancel a queued or running job
  help [<command>]  Print help for spoolctl or one of its commands

Options:
  -j, --json        Print output as JSON
  -h, --help        Print help
  -V, --version     Print version

See spoolctl(8).
```

Indent entries by two spaces, and align the descriptions in a column at
least two spaces after the longest entry. Keep every line within 80
columns, or wrap to the terminal width when the parser does that.

## Usage lines

Write one usage form per line. When there are several, start the first on
the `Usage:` line and indent the rest to line up under it:

```text
Usage: spoolq list [--all]
       spoolq submit <file>
       spoolq cancel <job-id>
```

A program with many commands gives one general form, `<command>`, and lists
the commands in the `Commands:` section instead.

## Entries and descriptions

Write each description as a fragment that starts with a capital letter and
a verb in the imperative, with no final period: "Print output as JSON", not
"prints output as JSON." or "Output format". These are the same rules Core
Style gives for list items, and they match clap's own "Print help" and
"Print version".

Write placeholders in lowercase, in angle brackets, and hyphenated, as Core
Style requires: `<job-id>`, not `JOB_ID` or `<JOB-ID>`. Put optional parts
in square brackets. clap uppercases placeholders by default, so set the name
of each one explicitly.

Show the short and long forms of an option together, short first, and the
placeholder after the long form: `-f, --format <format>`. When an option
has a default, end its description with it in parentheses:
`Set the output format (default: text)`.

List commands and options in the same order as the man page, with `-h,
--help` and `-V, --version` last.

## Required flags

Every first-party program accepts these flags, including daemons:

| Flag | Prints | Stream | Exit status |
|---|---|---|---|
| `-h`, `--help` | The help | stdout | 0 |
| `-V`, `--version` | The program name and package version, such as `spoolctl 0.4.2` | stdout | 0 |

`-h` and `--help` print the same text. Don't give `--help` a longer version.

A program with commands also accepts `help` and `help <command>`, and
`<command> --help` prints the same text as `help <command>`. A command's help
follows the same layout, with a usage line for that command alone.

Running a program with commands and no arguments is a usage error, unless
the man page documents a default command.

## Error messages

Print every error to stderr, as one line in this form:

```text
<program>: <what went wrong>
```

Use the name the program was invoked as, without its directory. A
multicall binary uses the applet name.

Name the thing that failed before saying what went wrong, separated by a
colon, so the reader sees the object first:

```text
reg: Machine\System\Spooler: access denied
spoolctl: cancel 4127: no such job
```

- **Start in lowercase**, unless the first word is a proper noun or an
  identifier.
- **End without a period.**
- **Don't add a prefix** such as `Error:` or `error:`. The program name
  already marks the line as a message from the program.
- **Quote a value the reader supplied** with straight single quotes when it
  appears mid-message: `spoolctl: unknown command 'stauts'`. Don't quote it
  when it is the object at the start of the message.
- **Keep the system's own wording** for an error from the operating system,
  such as `No such file or directory`, so first-party messages match those
  of adopted tools. Don't add an error number such as `(os error 2)`.
- **Never print a debug representation**, such as Rust's `{:?}` output or a
  stack trace. A Rust `main` that returns `Result` prints `Error:` and the
  debug form, so handle the error and print the message instead.

When the reader can fix the problem and the fix isn't obvious, add one line
after the error, with no program-name prefix, saying what to do. Write it as
a sentence, ending in a period.

### Warnings

Print a warning to stderr as `<program>: warning: <message>`, following the
same rules. A warning doesn't change the exit status.

### Usage errors

A usage error is a problem with the arguments: an unknown option, a missing
argument, or a value of the wrong form. Print the error, then this line, to
stderr:

```text
spoolctl: unknown option '--jsno'
Try 'spoolctl --help' for more information.
```

Don't print the full help after a usage error; it pushes the error off the
screen. The one exception is running a program with commands and no
arguments, which prints the help to stderr in place of an error message.

Neither clap nor uucore prints usage errors in this form by default, so
render them yourself: use the error's kind and context to build the
message.

## Exit statuses

| Status | Meaning |
|---|---|
| 0 | Success, including printing help or the version |
| 1 | Failure |
| 2 | Usage error |

A program can define more specific failure statuses, from 3 upward, and
lists them in the man page's EXIT STATUS section. Don't use 2 for anything
but a usage error.

## The pointer line

End the help with a pointer to the full documentation:

- **A program installed on Peios** points to its man page: `See spoolctl(8).`
- **A tool that runs on a developer's machine**, such as pekit, points to its
  learn page by URL, because the man page might not be installed there.

Don't point to a path in a source repository. It doesn't exist on an
installed system.
