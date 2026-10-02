---
title: Message Reference
description: Every line on the editing channel, in order, with an example conversation.
---

| Direction | Line | Defined in |
|---|---|---|
| Requester → editor | The request (first line, no `type`) | §8.4 |
| Editor → requester | `{"type":"apply","sd":…,"parts":[…]}` | §8.5 |
| Requester → editor | `{"type":"applied"}` | §8.5 |
| Requester → editor | `{"type":"failed","why":…}` | §8.5 |

## An example

A file explorer opens the permissions of a file. The person adds
Everyone with Read and presses Apply, which fails, then changes their
mind and closes the dialog. Lines are shown on several lines here for
reading. On the channel each is one line, and the descriptors are
shortened.

```
→ {"object":{"name":"notes.txt","kind":"File","container":false},
   "sd":"AQAEgBQAAAAkAAAAAAAAADQAAAAB…",
   "rights":[{"name":"Full control","mask":2032127,"general":true},
             {"name":"Read","mask":1179785,"general":true}],
   "generic":{"read":1179785,"write":1179926,"execute":1179808,"all":2032127},
   "can":{"owner":true,"audit":false}}
← {"type":"apply","sd":"AQAEgBQAAAAkAAAAAAAAADQAAAAC…","parts":["dacl"]}
→ {"type":"failed","why":"you are not allowed to"}
```

The editor shows why and stays open. The person closes it, and the
requester reads end-of-file on the editor's output.
