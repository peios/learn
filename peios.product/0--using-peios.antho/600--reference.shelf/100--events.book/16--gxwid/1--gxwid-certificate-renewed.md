---
title: "gxwid.certificate.renewed"
description: "gxwid made the machine a new certificate for its GXWI key and serves it from now on, in place of the one before."
---

- **Event type:** `gxwid.certificate.renewed`
- **Defined in:** `gxwid.evman`
- **Tier:** essential
- **Gating:** none — every renewal of the machine's GXWI certificate is recorded
- **Cardinality:** once per renewal, which is about once a year

gxwid made the machine a new certificate for its GXWI key and serves it
from now on, in place of the one before. A certificate lasts a year and is
renewed once fewer than 30 days of it remain, which gxwid looks for as it
starts, once a day, and when it is reloaded; one made by an older gxwid
that lasts longer, or one not valid yet, is renewed at the first look.

The key is the same, so the machine's identity is: what changes is the
certificate's fingerprint, which a browser that trusted the old
certificate does not know. Everyone who reaches the desktop is shown the
browser's warning once more, and anyone who imported the old certificate
imports the new one, `/var/state/gxwi/certificate.pem`. This record says
which fingerprint they should now see.

Essential because it changes what everyone who connects is shown, and is
rare. The new certificate is served to every connection made after it;
those already made, and everyone signed in, carry on.

No subject: gxwid renews the certificate of its own accord, on time.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`object.certificate.digest`](~peios/events/field-index/fields-object#object.certificate.digest) | `bin` | required | The new certificate's SHA-256 digest. |
| [`object.certificate.digest-previous`](~peios/events/field-index/fields-object#object.certificate.digest-previous) | `bin` | required | The SHA-256 digest of the DER encoding of the certificate this one replaced: its fingerprint, as 32 bytes, in the form of `object.certificate.digest`. |
| [`object.certificate.name`](~peios/events/field-index/fields-object#object.certificate.name) | `str` | required | The new certificate's subject, `CN=` the machine's name when it was made and `O=Peios`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `gxwid.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
