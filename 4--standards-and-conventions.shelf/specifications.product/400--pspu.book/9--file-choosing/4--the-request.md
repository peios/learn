---
title: The Request
description: The first line — whether to open or save, what the dialog is called and what the file is for, where to start, the name to suggest, and the kinds of file to offer.
---

The request is a JSON object, sent once, as the first line.

| Member | Type | Required | Meaning |
|---|---|---|---|
| `mode` | string | yes | `open` for an existing file to read; `save` for a place and a name to write to |
| `title` | string | yes | What the dialog is called, for the person: "Export a key" |
| `purpose` | string | no | What the file is for, in a sentence, for the person to read |
| `folder` | string | no | An absolute path to the folder to start in |
| `name` | string | no | The name to suggest, in `save` mode: "Services.json" |
| `filters` | array | no | The kinds of file to offer, in order, each an object below |

Each filter is an object with:

| Member | Type | Meaning |
|---|---|---|
| `name` | string | What the kind is called, for the person: "Registry documents" |
| `extensions` | array of strings | The extensions it covers, without the dot: `["json"]` |

## What the chooser does with it

The chooser MUST start in `folder` if it is given, absolute, and a folder
the person may list, and otherwise in the person's home folder.

If `filters` is given, the chooser MUST offer them in the order given,
with the first chosen at first, and MAY offer every file as well. In
`open` mode it SHOULD show only folders and the files of the kind
chosen. A filter matches a file by its extension, without regard to
case.

In `save` mode the chooser MUST offer `name`, if given, as the name to
save as, and the person MAY change it. If the person types a name
without an extension while a filter is chosen, the chooser SHOULD add
the filter's first extension.

The requester MUST NOT rely on the person choosing a file of a kind it
offered: the person may choose any file. A requester that needs a kind
checks what it opens.

A chooser that receives a request it cannot use, because a required
member is missing or `mode` is unknown, MUST NOT show a dialog, and ends
without answering.
