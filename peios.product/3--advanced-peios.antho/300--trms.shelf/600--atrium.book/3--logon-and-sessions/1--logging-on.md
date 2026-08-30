---
title: Logging On
description: The login page is a rendering of authd's prompts — atriumd is a PGSS Logon client with a browser for a terminal.
---

Atrium adds no authentication of its own. Logging on through the
browser is a PGSS Logon conversation (PGSS §2) with authd, conducted
by atriumd, with the browser standing where a terminal would.

A browser with no valid cookie gets the login page from atrium-server
— the one page the server itself owns, since before a logon there is
no session to serve anything. The page collects a username and posts
it; from there:

1. atriumd connects to `/run/logon.sock` and sends `LogonStart`,
   authored by atriumd itself: logon type Network, the username, and
   the client address as the unverified remote host. The browser
   proposes nothing.
2. authd's credential requests are relayed outward as JSON — the page
   renders whatever prompts arrive, with no assumption that the answer
   is a password — and the answers travel back the same way.
3. On `AccessGranted`, the token descriptor stays in atriumd's session
   table; it never travels further. atriumd submits the session host
   (§3.2), hands the server the session's socket, and the server mints
   a cookie.
4. On `AccessDenied`, a retryable denial is shown to the browser as
   one uniform "Incorrect username or password"; the specific denial
   goes to the log. Non-retryable denials are shown as given.

The cookie is 256 bits from the kernel's entropy pool, hex-encoded,
`HttpOnly` and `SameSite=Strict`. It is a bearer: whoever holds it is
the session, which is why it goes into the cookie jar and nowhere
else — not to session hosts, not into JavaScript. One cookie binds one
browser to one interactive session; logging out discards both the
cookie and the session.

Passwords cross the network unencrypted in this version, as does
everything else; the deployment posture is a trusted network segment
until TLS lands.
