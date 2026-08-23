---
title: The Relayed Interrogation
description: CredentialRequest and CredentialResponse carrying PGSS Logon bodies verbatim — what the authority polices on the way through, and what it never inspects.
---

Two messages, both carrying PGSS Logon bodies verbatim.

## CredentialRequest

`msg_type` = `0x8002`. Source to authority. Body is PGSS §2.8's
`CredentialRequest`, byte-for-byte.

The source decides what to ask for, in what order, and over how many
rounds. The authority relays it to the client.

## CredentialResponse

`msg_type` = `0x0003`. Authority to source. Body is PGSS §2.8's
`CredentialResponse`, byte-for-byte.

## What the authority polices

The authority relays, but does not relay *anything*.

**An authority MUST refuse to relay a prompt whose credential type is
absent from the client's `supported_credential_types`.** PGSS §2.8 makes
this the authority's obligation towards the client, and it holds however
the authority reached the prompt — a prompt originating in a source is
still the authority's to police.

Relaying it would force the client to hard-fail, and a client that
guessed instead might echo a secret to the screen. The authority MUST
terminate the logon instead.

An authority MUST also enforce its own round and time limits on the
relayed exchange (PGSS §2.3), independently of any the source applies. A
source that never terminates a conversation MUST NOT be able to hold a
client's logon open indefinitely.

## Credential handling

The obligations of PGSS §2.12 bind both parties on this leg as they do
on the client's. Credential material reaching a source has been decoded
and re-encoded once more than it would have been without federation, and
every buffer it passed through on the way is one the obligation covers.

## What the authority does not do

It does not interpret prompts, rewrite messages, reorder anything, or
synthesise a request of its own. A source's prompt reaches the client as
the source wrote it, which is the property that makes adding a
credential type a change to sources alone.
