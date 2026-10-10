---
title: The machine's certificate
type: how-to
description: GXWI serves the desktop over HTTPS with a certificate each machine makes for itself and renews every year — why the browser warns, how to check the fingerprint before going past the warning, how to stop the warning by importing the certificate, and where the key is kept.
related:
  - peios/desktop-settings/for-all-users
  - peios/disks-and-filesystems/installing-to-disk
  - peios/disks-and-filesystems/first-boot-setup
  - peios/trust/overview
---

The desktop is reached in a browser at `https://` and the machine's address,
port 7780 unless an administrator has chosen another. GXWI serves it over
HTTPS alone, with a certificate the machine made for itself the first time GXWI
started. No certificate authority has vouched for it, so a browser warns the
first time it is opened, until it is told to trust it.

Opening `http://` instead is answered with a redirect to the same address under
`https://`, and with nothing else: no page is ever served without encryption.

## Check the fingerprint before going past the warning

The warning is the browser saying it cannot tell this certificate from one
someone between you and the machine made up. You can: every certificate has a
SHA-256 fingerprint, and the machine shows you its own.

Sign in at the machine's own console — on a live medium, as `peios`, which
needs no password — and print the fingerprint, which any account may read:

```
$ cat /var/state/gxwi/certificate.sha256
B8:39:98:AB:E7:F6:64:25:BC:0D:DE:56:F4:78:2E:21:3D:D8:AB:FF:EF:78:8A:81:6E:94:99:17:94:83:73:C3
```

Read it there, and not from a page in the browser: a page that came over the
connection you are checking would show whatever someone in the middle of it
wanted. Once you trust the connection, a terminal on the desktop reads the same
file.

In the browser, open the warning's details and view the certificate. Its
SHA-256 fingerprint is the same 32 pairs of hex digits, though some browsers
separate them with spaces rather than colons. If the two match, the connection
is to this machine and nobody can read it on the way. If they do not, do not
sign in.

## Stop the warning

The certificate is in `/var/state/gxwi/certificate.pem`, also readable by
anyone. Copy it to the device you browse from and add it to that browser's or
that system's trusted certificates; the browser then opens the machine with no
warning.

The certificate names the machine as it was called when the certificate was
made, and `localhost`. It does not name the machine's addresses, which are not
known when the certificate is made and can change. A browser that trusts the
certificate still warns when the machine is opened by an address or a name the
certificate does not carry.

An imported certificate lasts until the machine renews it, once a year (see
[Renewal](#renewal)): import the new one then.

A certificate only gone past at the warning, not imported, also costs the
**waiting page**: GXWI keeps a page in the browser that it shows while the
machine is restarting or cannot be reached, and a browser keeps such a page
only for a certificate it trusts. Without it, a tab left open while the machine
restarts shows the browser's own error, and loads again by hand.

## No HSTS

GXWI deliberately sends no `Strict-Transport-Security` header. HSTS tells a
browser to refuse any certificate warning for the site from then on, which with
a certificate of the machine's own making would leave nobody a way past the
first warning, including after the machine's key changes.

## Where the key is kept

| File | What it is | Who can read it |
|---|---|---|
| `/var/state/gxwi/key.pem` | The private key, ECDSA P-256 | SYSTEM alone |
| `/var/state/gxwi/certificate.pem` | The certificate | Everyone |
| `/var/state/gxwi/certificate.sha256` | Its SHA-256 fingerprint | Everyone |

GXWI makes the key once and keeps it. It never replaces a key it cannot read:
it stops, and says so. Move the files aside to have a new key made; every
browser that trusted the old certificate then warns again.

## Renewal

A certificate lasts a year, from the day before it was made. GXWI renews it
once fewer than 30 days of it remain, for the same key: the machine is the same
machine, but the certificate, and so its fingerprint, is new. Each renewal
means one more warning in every browser that went past the old one, and
importing the new `certificate.pem` again for anyone who imported the old.
Check the new fingerprint as you did the first.

GXWI looks when it starts, once a day while it runs, and when it is reloaded:

```
$ svctl reload gxwid
```

Nothing restarts, and nobody signed in is signed out. Connections already open
carry on; the next one the browser makes is shown the new certificate. A
renewal is recorded as the event
[`gxwid.certificate.renewed`](~peios/events/gxwid/gxwid-certificate-renewed),
which carries the old and new fingerprints.

On a live medium `/var/state` is in memory, so every boot makes a new key and
the warning comes back each time. Installing carries the medium's key into the
installed system, from either installer, so the browser that installed the
machine goes on trusting it through first-boot setup. A system installed with
`peios-install` makes its own key when GXWI first starts.
