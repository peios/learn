---
title: Message Reference
description: Every line on the editing channel, in order, with an example conversation.
---

| Direction | Line | Defined in |
|---|---|---|
| Requester → editor | The request (first line, no `type`) | §8.4 |
| Editor → requester | `{"type":"apply","sd":…,"parts":[…],"propagate":…}` | §8.5 |
| Requester → editor | `{"type":"progress","done":…,"at":…}` (while pushing into what is inside; no answer) | §8.5 |
| Editor → requester | `{"type":"stop"}` (while pushing into what is inside; no answer) | §8.5 |
| Requester → editor | `{"type":"applied","done":…,"failed":[…],"stopped":…}` (the last three only after pushing) | §8.5 |
| Requester → editor | `{"type":"failed","why":…}` | §8.5 |

## An example

A file explorer opens the permissions of a file. The person adds
Everyone with Read and presses Apply, which fails, then changes their
mind and closes the dialog. Lines are shown on several lines here for
reading. On the channel each is one line, and the descriptors are
shortened.

```
→ {"object":{"name":"notes.txt","kind":"File","container":false,
             "parent":{"name":"/home/dana","sd":"AQAEgBQAAAAkAAAA…"}},
   "sd":"AQAEgBQAAAAkAAAAAAAAADQAAAAB…",
   "read":["owner","group","dacl","label"],
   "rights":[{"name":"Full control","mask":2032127,"general":true},
             {"name":"Read","mask":1179785,"general":true}],
   "generic":{"read":1179785,"write":1179926,"execute":1179808,"all":2032127},
   "can":{"owner":true,"audit":false,"label":true}}
← {"type":"apply","sd":"AQAEgBQAAAAkAAAAAAAAADQAAAAC…","parts":["dacl"]}
→ {"type":"failed","why":"you are not allowed to"}
```

The editor shows why and stays open. The person closes it, and the
requester reads end-of-file on the editor's output.

The requester could read the label but not the rest of the SACL, so
`read` names `label` and not `sacl`, and the SACL in `sd` holds the
label alone. Had the person raised the label, the editor would have
sent `"parts":["label"]`.

## Pushing into what is inside

The same explorer opens a folder's permissions, saying it can push into
what is inside. The person gives Finance Modify on the folder and
everything in it, presses OK, says yes to updating what is already
inside, and stops partway.

```
→ {"object":{"name":"finance","kind":"Folder","container":true}, …,
   "can":{"owner":true,"audit":true,"label":true,"propagate":true}}
← {"type":"apply","sd":"AQAEnBQAAAAkAAAA…","parts":["dacl"],"propagate":true}
→ {"type":"progress","done":120,"at":"/srv/finance/2025/q3.xlsx"}
→ {"type":"progress","done":480,"at":"/srv/finance/2026/budget"}
← {"type":"stop"}
→ {"type":"applied","done":512,
   "failed":[{"name":"/srv/finance/archive","why":"you are not allowed to"}],
   "stopped":true}
```

The folder's DACL was applied, and 512 items inside were updated before
the walk stopped. The editor shows that, and what could not be done, and
stays open though OK was pressed. The person can push the rest with
another `apply` of the same `parts`.
