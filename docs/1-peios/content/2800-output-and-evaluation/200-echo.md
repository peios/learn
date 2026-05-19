---
title: echo
type: reference
description: Print arguments as a line of text to standard output.
related:
  - peios/output-and-evaluation/printf
  - peios/output-and-evaluation/overview
---

`echo` prints its arguments, separated by single spaces, followed by a newline.

```
echo [options] [string...]
```

```
$ echo Hello, Peios
Hello, Peios
```

It is the simplest way to put a line of text on standard output — printing a message, or feeding a fixed string into a pipe.

## Options

| Option | Effect |
|---|---|
| `-n` | Do not print the trailing newline. |
| `-e` | Interpret backslash escape sequences in the arguments (see below). |
| `-E` | Do **not** interpret escape sequences. This is the default. |

## Escape sequences

With `-e`, `echo` recognises these backslash sequences and prints the character they stand for:

| Sequence | Character |
|---|---|
| `\\` | A literal backslash. |
| `\n` | Newline. |
| `\t` | Horizontal tab. |
| `\r` | Carriage return. |
| `\b` | Backspace. |
| `\f` | Form feed. |
| `\v` | Vertical tab. |
| `\a` | Alert (the terminal bell). |
| `\e` | Escape. |
| `\0NNN` | The byte with octal value `NNN`. |
| `\xHH` | The byte with hexadecimal value `HH`. |
| `\c` | Stop — produce no further output. |

## `echo` and `printf`

`echo` is fixed: arguments, spaces, a newline. The moment you need *control* over the output — columns, padding, a number formatted a particular way, output with no spaces between pieces — reach for [`printf`](~peios/output-and-evaluation/printf) instead. `printf` is also more predictable across environments, since `echo`'s handling of escapes and `-n` varies.

## Exit status

`echo` returns `0` unless it cannot write its output.
