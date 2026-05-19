---
title: realpath
type: reference
description: Resolve a path to its canonical, absolute form — every symbolic link followed and every . and .. component removed.
related:
  - peios/listing-and-paths/readlink
  - peios/listing-and-paths/overview
---

`realpath` resolves a path to its **canonical** form: absolute, with every symbolic link followed and every `.` and `..` component removed. Given any path, it tells you the one true location it refers to.

```
realpath [options] file...
```

```
$ realpath ../work/./notes.txt
/data/projects/jack/notes.txt
```

A single file can be named many ways — through links, through relative paths, with redundant components. `realpath` reduces all of them to the single canonical path, which makes it the right tool for comparing two paths, or for turning a path a user typed into one a script can rely on.

## How much must exist

By default `realpath` requires every component of the path *except the last* to exist. These options change that requirement:

| Option | Existence requirement |
|---|---|
| (default) | Every component except the last must exist. |
| `-e`, `--canonicalize-existing` | Every component must exist — including the final one. |
| `-m`, `--canonicalize-missing` | No component need exist. The path is canonicalized purely as text where it cannot be walked. |

## How symbolic links are handled

| Option | Effect |
|---|---|
| `-P`, `--physical` | Resolve each symbolic link as it is encountered. This is the default. |
| `-L`, `--logical` | Resolve `..` components *before* resolving the symbolic links they follow. |
| `-s`, `--strip`, `--no-symlinks` | Do not resolve symbolic links at all — only remove `.` and `..` components. The result is canonical as text, but a link in the path is left as-is. |

## Output options

| Option | Effect |
|---|---|
| `--relative-to=DIR` | Print the result as a path relative to `DIR` instead of as an absolute path. |
| `--relative-base=DIR` | Print an absolute path, unless the result lies inside `DIR`, in which case print it relative to `DIR`. |
| `-z`, `--zero` | End each output line with a NUL character instead of a newline. |
| `-q`, `--quiet` | Do not print a warning when a path is invalid. The exit status still reports the failure. |

## `realpath` and `readlink`

[`readlink`](~peios/listing-and-paths/readlink) with `-f`/`-e`/`-m` does the same canonicalizing job. The difference is focus: `readlink` is primarily for reading a single link's target, with canonicalizing as an extra; `realpath` is built for canonicalizing and carries the richer option set — relative output, the symlink-handling modes, the strip-only mode. Reach for `realpath` when canonicalizing is the actual goal.

## Exit status

| Code | Meaning |
|---|---|
| `0` | Every path was resolved and printed. |
| `1` | A path could not be resolved under the chosen options. |
