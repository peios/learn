---
title: Message Reference
description: Every line on the choosing channel, in order, with an example conversation.
---

| Direction | Line | Defined in |
|---|---|---|
| Requester → chooser | The request (first line, no `type`) | §9.4 |
| Chooser → requester | `{"type":"chosen","path":…}` | §9.5 |
| Chooser → requester | `{"type":"cancelled"}` | §9.5 |

## An example

A registry editor exports a key. The person goes into a folder, makes a
folder called Backups inside it, opens it, keeps the suggested name and
saves. Lines are shown on several lines here for reading. On the channel
each is one line.

```
→ {"mode":"save","title":"Export Services",
   "purpose":"The key and everything under it is written to a registry document.",
   "folder":"/home/dana","name":"Services.json",
   "filters":[{"name":"Registry documents","extensions":["json"]}]}
← {"type":"chosen","path":"/home/dana/Backups/Services.json"}
```

The chooser ends, and the registry editor writes the file.
