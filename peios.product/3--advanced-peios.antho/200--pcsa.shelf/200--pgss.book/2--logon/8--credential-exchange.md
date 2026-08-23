---
title: Credential Exchange
description: CredentialRequest and CredentialResponse — messages, prompts, the client capability rule, and what an empty request means.
---

## CredentialRequest

`msg_type` = `0x8001`. Authority to client.

| Field | Encoding | Limit |
|---|---|---|
| `messages` | array of *Message* | 8 |
| `prompts` | array of *Prompt* | 16 |

**Message:**

| Field | Encoding | Limit |
|---|---|---|
| `severity` | `u8` | §2.B |
| `text` | string | 512 |

**Prompt:**

| Field | Encoding | Limit |
|---|---|---|
| `credential_ref` | `u32` | — |
| `credential_type` | `u8` | §2.B |
| `credential_name` | string | 128 |

Both arrays MAY be empty.

### Messages

Text for the principal to read, before any prompt is presented. "Your
password expires in three days"; "Authenticating against the local
source".

A client MUST display messages it receives, in order, before the prompts
in the same request. It MUST NOT interpret them, and MUST NOT vary its
behaviour on their content.

### Prompts

Each prompt asks for one piece of credential material.

`credential_ref` identifies the prompt within the conversation. The
client echoes it back unchanged in its answer. It MUST be unique among
the prompts of a single request. An authority MAY reuse a value in a
later round.

`credential_name` is what to show the principal — "Password",
"Verification code". It is a display string. A client MUST NOT branch on
it; `credential_type` is what says how to collect the answer.

### The client capability rule

An authority **MUST NOT** send a prompt whose `credential_type` is
absent from the client's `supported_credential_types` (§2.7).

This is a hard requirement rather than a courtesy. A client that
receives a prompt it cannot render has no good option: failing the logon
punishes the principal for a mismatch neither party chose, and *guessing*
— collecting a line of text for a credential type that is not a password
— may echo a secret to the screen. An authority that cannot proceed
within the client's declared capabilities MUST deny the logon instead.

A client that nevertheless receives an unrenderable prompt MUST fail the
conversation rather than guess.

### Empty requests

A `CredentialRequest` with no prompts is valid. It carries messages
only, and the client MUST answer it with a `CredentialResponse` carrying
no answers. This is how an authority conveys information mid-conversation
without asking for anything.

## CredentialResponse

`msg_type` = `0x0002`. Client to authority.

| Field | Encoding | Limit |
|---|---|---|
| `answers` | array of *Answer* | 16 |

**Answer:**

| Field | Encoding | Limit |
|---|---|---|
| `credential_ref` | `u32` | — |
| `data` | length-framed bytes | 32768 |

`credential_ref` MUST match a prompt from the request being answered.
`data` is the material the principal supplied — opaque bytes, no
encoding implied.

A client SHOULD answer every prompt it was given. An authority MUST NOT
assume it has: a missing answer is a failed logon, not a protocol
violation, and MUST be treated as such rather than as grounds to tear
down the connection.

An authority MUST match answers to prompts by `credential_ref` and MUST
NOT rely on ordering.

Both parties encode and decode this message under the obligations of
§2.12. The encoded message holds the credential just as much as the
`data` field inside it does.

> [!NOTE]
> A client that cannot collect an answer — the principal pressed escape
> — MAY send a response omitting it rather than closing the connection.
> That gives the authority the opportunity to deny cleanly with a reason
> the principal can read.
