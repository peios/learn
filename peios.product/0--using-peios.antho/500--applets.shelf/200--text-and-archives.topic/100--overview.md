---
title: Text and archive tools
type: guide
description: Inspect text, select files, compare contents and work with archives in Experimental.
---

Experimental includes the following commands in the system root. They are not
part of the initramfs tool set.

| Task | Commands | Package |
|---|---|---|
| Search text | `grep`, including `grep -E`, `grep -F` and `grep -P` | `org.gnu.grep` |
| Transform lines | `sed` | `org.gnu.sed` |
| Process fields and records | `awk`, `gawk` | `org.gnu.gawk` |
| Select files and pass arguments | `find`, `xargs` | `org.gnu.findutils` |
| Compare files | `diff`, `cmp`, `diff3`, `sdiff` | `org.gnu.diffutils` |
| Read long files interactively | `less` | `com.greenwoodsoftware.less` |
| Identify file contents | `file` | `com.darwinsys.file` |
| Create and extract tar archives | `tar` | `org.gnu.tar` |
| Gzip compression | `gzip`, `gunzip`, `zcat` | `org.gnu.gzip` |
| XZ compression | `xz`, `unxz`, `xzcat` | `org.tukaani.xz` |
| Zstandard compression | `zstd`, `unzstd`, `zstdcat` | `com.facebook.zstd` |
| Bzip2 compression | `bzip2`, `bunzip2`, `bzcat` | `org.sourceware.bzip2` |
| Create ZIP archives | `zip` | `net.sourceforge.infozip.zip` |
| Inspect and extract ZIP archives | `unzip`, `zipinfo` | `net.sourceforge.infozip.unzip` |

Peiosutils supplies the other basic text commands, including `cat`, `head`,
`tail`, `sort`, `uniq`, `cut`, `paste`, `join`, `tr` and `wc`.

## Inspecting text

```sh
grep -n 'error' output.txt
awk '{ print $1 }' records.txt
diff before.txt after.txt
less output.txt
```

In `less`, use Space to move forward, `b` to move back, `/pattern` to search,
`n` for the next match and `q` to quit. The pager does not install an editor;
its edit command requires a separately installed editor.

## Working with archives

GNU tar invokes the separate compressor commands included above. The matching
compression libraries alone do not provide those commands.

```sh
tar -caf backup.tar.xz documents/
tar -tf backup.tar.xz
mkdir restored
tar -xf backup.tar.xz -C restored

zip -r documents.zip documents/
unzip -l documents.zip
unzip documents.zip -d restored-zip
```

Use `.tar.gz`, `.tar.xz`, `.tar.zst` or `.tar.bz2` with `tar -a` to choose the
compressor by suffix. `file archive` identifies a file by its contents.

These formats exchange file contents and conventional archive metadata. Do not
use them as a substitute for a Peios system backup that preserves native
security descriptors and registry state.
