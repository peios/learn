---
title: Editing with Nano
type: how-to
description: Save a document and interpret the Peios port's private backup, recovery, and history behavior.
---

The `org.gnu.nano` package supplies nano and rnano. Its common package
supplies
syntax definitions, translations, and manuals. The vendor nanorc enables
bundled syntax definitions. HOME and XDG data conventions select user state.

## Edit and check a document

1. Open `nano path/to/file`. Use Ctrl+G for help.
2. Edit the intended buffer. Ctrl+O writes it; Enter confirms the filename.
3. Confirm the write succeeded before Ctrl+X exits. Check the saved contents
   when recovery or an external writer makes the result uncertain.

An existing regular file is written in place. Its owner, DACL, audit policy,
and integrity label remain, and hardlinks still refer to that object. This
is not atomic replacement or a guarantee against interrupted storage writes.
New documents use destination inheritance. FACS controls access; numeric root
and Unix modes do not grant permission. Saving does not itself require
permission to rewrite the descriptor, while synchronization needs its
applicable handle right.

## Choose backup and recovery behavior

`nano --backup file` requests a backup, normally `file~`. Backups, emergency
`.save` files, and formatter/speller scratch files are private to the
effective token's user SID before contents are written. They do not clone
the document's sharing policy or ownership. Normal mandatory and audit
controls still apply.

On a hangup or fatal error nano attempts an emergency save and reports its
path on success. Space, directory authority, and private-creation failures
can prevent it. There is no fallback to Unix `0600`. If backup fails, the
prompt lets the user decide whether to save the original without a backup;
do not mistake that choice for a successful recovery copy.

## History and lock files

Search/replace/command history and cursor-position history are optional,
selected by `--historylog` and `--positionlog`. nano uses a suitable existing
`~/.nano` or its XDG/default local-data directory. Its private state policy
must already hold for existing files and directories. It validates opened
files and refuses symlinks, multiple hardlinks, and incompatible policy
rather than silently changing permissions. A history error disables the
affected operation without disabling ordinary editing.

Advisory lock files use nano's interoperable format and normal inheritance.
They expose editing identity/path metadata, not buffer contents, and do not
authorize access. rnano's restricted editing mode also grants no new native
authority.
