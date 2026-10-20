---
title: Working with Text and Archives
type: how-to
description: Choose text tools, inspect archives, and extract contents without treating conventional metadata as a native backup.
---

Install the tools needed for the task. Package availability in the system
root does not imply availability in an initramfs.

## Inspect and compare

Use `grep` for matching lines, `sed` for line transformations, `awk` or `gawk`
for fields and records, and `find` with `xargs` for selecting files and
passing
arguments. `diff`, `cmp`, `diff3`, and `sdiff` compare contents. Peiosutils
supplies basic tools including `cat`, `head`, `tail`, `cut`, `paste`, `join`,
`sort`, `uniq`, `tr`, and `wc`.

```sh
grep -n 'error' output.txt
awk '{ print $1 }' records.txt
diff before.txt after.txt
less output.txt
```

In `less`, Space advances, `b` goes back, `/pattern` searches, `n` repeats the
search, and `q` quits. Its edit command needs a separately installed editor.
For terminal editing and its save/recovery rules, see
[Editing With nano](~peios/command-line-basics/editing-with-nano).

## Create, inspect, and extract

1. Choose a format supported by the recipient and install its compressor
   command as well as the archive tool. A compression library alone does
   not provide the executable GNU tar invokes.
2. Create and inspect an archive:

   ```sh
   tar -caf backup.tar.xz documents/
   tar -tf backup.tar.xz
   ```

3. Extract into a fresh directory and inspect the resulting contents:

   ```sh
   mkdir restored
   tar -xf backup.tar.xz -C restored
   ```

GNU tar's `-a` selects compression by suffix, such as `.tar.gz`, `.tar.xz`,
`.tar.zst`, or `.tar.bz2`. The associated commands are gzip, XZ, Zstandard,
and bzip2. `file ARCHIVE` identifies contents independently of the name.

For ZIP exchange, use `zip -r documents.zip documents/`, inspect with
`unzip -l documents.zip`, then extract with
`unzip documents.zip -d restored-zip`.
These formats carry conventional metadata and contents, not a complete
Peios
backup of native security descriptors and registry state.
