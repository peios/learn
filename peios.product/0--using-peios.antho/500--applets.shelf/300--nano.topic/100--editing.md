---
title: Editing files with nano
type: guide
description: Edit text and understand nano's saving, backup and recovery behavior on Peios.
---

Experimental includes GNU nano in the system root through `org.gnu.nano`.
Run `nano path/to/file`. Press **Ctrl+O** to write the buffer, **Enter** to
confirm its filename, and **Ctrl+X** to exit. **Ctrl+G** opens help.

Syntax definitions, translations and manuals are in `org.gnu.nano-common`.
The vendor `/usr/etc/nanorc` enables the bundled syntax definitions. Normal
nano user configuration and `HOME`/`XDG_DATA_HOME` conventions apply. `rnano`
is also supplied; its restricted editing mode does not grant additional
Peios authority.

## Saving documents

Saving an existing regular file writes into the existing object. Its owner,
DACL, audit policy and integrity label remain unchanged. Hardlinks continue to
refer to that object. A new document receives the destination's normal Peios
security inheritance. Saving in place is not an atomic replacement and does
not guarantee recovery from a storage failure during the write.

FACS decides whether saving is permitted. Unix mode bits and a numeric root
UID do not grant access. Editing does not require permission to change the
file's security descriptor; synchronizing a save requires the applicable
handle synchronization right.

## Backups, recovery and history

Use `nano --backup file` to retain a backup, normally `file~`. Peios nano
creates backups, emergency `.save` files and formatter/speller scratch files
with a protected DACL granting access to the effective token's user SID.
Backups are private editor copies; they do not clone the original document's
sharing policy or ownership. Normal kernel integrity/audit rules still apply.
No file contents are written before the private security is established.

History is optional: `--historylog` records search/replace/command history;
`--positionlog` remembers cursor positions. Nano uses an existing suitable
`~/.nano` directory or its usual `$XDG_DATA_HOME/nano` / `~/.local/share/nano`
location. Its state directory and files must have nano's private owner/DACL
policy. Peios nano checks the actual opened file before reading or truncating
it and refuses symbolic links, multiply linked files and incompatible policies.
It does not silently change the permissions of existing history. An unsafe
state directory or file produces an error and disables the affected history
operation; ordinary document editing remains available.

On a hangup or fatal error nano attempts an emergency save, subject to space,
namespace permissions and other normal failures. It reports the saved path
when successful. If private creation is unavailable, nano reports failure
rather than substituting Unix `0600` permissions. Its backup failure prompt
still lets you choose whether to save the original without a backup.

Optional advisory lock files retain nano's interoperable format and normal
destination inheritance. They contain editing identity/path information, not
buffer contents, and do not authorize access to the document.
