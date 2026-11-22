---
title: Windows
description: How a marker translates Windows' FILE_ATTRIBUTE_NOT_CONTENT_INDEXED to and from user.pgss.indexing.
---

Windows marks a file or directory with `FILE_ATTRIBUTE_NOT_CONTENT_INDEXED`
(0x00002000) to say its contents are not to be indexed. A marker that
serves files to Windows clients, such as an SMB server, SHOULD translate
it as follows.

**Reporting.** The marker reports the attribute set on an item that itself
carries `no-content`, `none`, or a value §8.2 reads as `no-content`. It
reports it clear on an item that carries `all` or no value. It reports
only the item's own word, not one it would take from a directory above.

**Setting.** When a client sets the attribute on an item whose own
preference is `all` or absent, the marker writes `no-content`. When the
item already carries `no-content` or `none`, the marker leaves the word
as it is.

**Clearing.** When a client clears the attribute, the marker removes the
item's attribute, so that the item takes its preference from above. It
does not write `all`.

**Not kept.** On a file system that cannot keep the attribute, the marker
MAY accept the client's request and keep nothing, as Windows programs set
attribute bits in passing and failing the request would fail a copy.

A marker that translates the attribute MUST NOT also offer
`user.pgss.indexing` to the client as a Windows extended attribute,
since the client would then see one preference twice.
