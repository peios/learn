---
title: SSH Public-Key Authentication
description: The implementation contract for principal-owned SSH credentials, including proof collection, transport binding, and a coordinated replacement of the unpublished formats.
---

The SSH public-key extension is implemented in authd/lpsd and the Peios
OpenSSH port. PEI-67 tracks its release qualification. PGSS/PSI version 1 and
the unpublished lpsd store layout were replaced together without a version
bump or migration. Rebuild consumers together and explicitly reprovision
old development stores; lpsd never resets an unreadable store automatically.

An SSH public key is a credential of a principal. The principal source
stores the authorized key and verifies proof of possession. The logon
authority constrains the originator, applies policy, derives the token,
and grants the logon. SSH does not introduce a second account authority.

The first source implementation is lpsd. No `.ssh/authorized_keys` lookup
is performed. Client private keys and server host keys are not principal
credential records; their storage is outside this extension.

## Responsibilities and trust

| Component | Responsibility |
|---|---|
| SSH client | Produces the standard SSH authentication signature using its private key |
| SSH transport and monitor | Establishes and retains the live transport binding; mediates credential collection |
| authd | Verifies the local originator, relays the credential exchange, enforces logon policy, and grants a token |
| lpsd | Owns local public-key credentials, checks their eligibility, verifies signatures, and asserts the principal |

A network-facing process does not receive authority to assert a principal
or obtain arbitrary logon tokens. The protected SSH monitor owns the PGSS
connection. A user session receives its resulting token, not the PGSS
connection, proof buffers, or monitor control channel.

Public-key verification does not replace disabled-account checks, logon
type restrictions, originator restrictions, or normal token derivation.
A valid signature alone never creates a session.

## Principal storage and policy

lpsd extends each principal with an explicit authentication policy and a
bounded list of SSH public-key records. The existing principal SID remains
the account identity; names, key comments, and fingerprints do not replace it.

Each key record contains:

| Field | Representation |
|---|---|
| Record ID | Random 128-bit identifier, stable until deletion |
| Public key | Validated, canonical SSH public-key blob; at most 8192 bytes |
| Label | UTF-8 text, at most 128 bytes; no control characters |
| Created time | UTC Unix seconds, recorded by lpsd |

The fingerprint is derived as SHA-256 of the canonical SSH public-key
blob and displayed in OpenSSH's `SHA256:` base64 form without padding.
It is not separately stored as an authority. Labels are display metadata,
not executable `authorized_keys` options. There are at most 32 keys per
principal; duplicate key material within a principal is rejected. The same
key may be deliberately enrolled on different principals, but a proof
for one username does not authenticate another.

The initial algorithm set is plain Ed25519 and RSA with `rsa-sha2-256`
or `rsa-sha2-512` signatures. RSA moduli are 3072–8192 bits. RSA key blobs
use the SSH `ssh-rsa` key format; that does not enable SHA-1 signatures.
DSA, SHA-1 signatures, certificates, security-key variants, and additional
key families are rejected until their semantics are specified. Malformed
keys, noncanonical encodings, trailing data, and unsupported types are
rejected at enrollment and at authentication. A maintained SSH key/crypto
implementation performs decoding and verification; no new cryptographic
primitive is introduced here.

Authentication policy has an explicit mode:

- `Credentials`: a nonempty set of permitted methods, initially
  `Password` and/or `SshPublicKey`. One permitted method is sufficient.
- `NoCredential`: authentication is intentionally unnecessary.
- `Denied`: no new authentication is permitted by this source.

The principal's separate enabled flag is checked first. In Credentials
mode, a permitted method without corresponding usable credential material
fails; it does not select another mode. In particular, deleting the last
key on a key-only principal leaves that principal unable to authenticate.
NoCredential mode is never inferred from an empty verifier or key list.

Initial enrollment is administrative, through lpsd's existing protected
administrative interface. The `lps key add`, `lps key list`, and
`lps key remove` operations operate on one principal and use its existing
administration authorization checks. Adding a key does not silently change
the principal's authentication policy. An explicit policy operation selects
password-only, key-only, either credential, NoCredential, or Denied.
NoCredential and Denied cannot be combined with credential methods.

Mutations are atomically persisted before success is acknowledged, using
the store's existing rollback-on-write-failure behavior. They invalidate
affected authentication state. Enrollment accepts a plain OpenSSH public
key line, including an optional label, but rejects private-key input and
`authorized_keys` options rather than silently ignoring them. Credential
inventory is not exposed through unauthenticated identity lookup.

Self-service enrollment and compound authentication such as password AND
key are separate extensions. Possessing a session token does not implicitly
authorize adding a persistent credential.

## Store replacement and revocation

The unpublished store layout is replaced in place, retaining its existing
format-version marker. The reader and writer implement only the replacement
layout; there is no old-store importer, dual reader, or downgrade path.
Development images and test stores are explicitly reprovisioned from updated
inputs rather than carried forward from an earlier build.

Provisioning writes an explicit policy for every principal. Password-bearing
fixtures use Credentials/Password; intentionally passwordless fixtures,
including the live image account, explicitly use NoCredential. Key-only
fixtures use Credentials/SshPublicKey with enrolled keys. An empty verifier
or key list never selects NoCredential automatically.

Unreadable, truncated, or malformed state still fails closed. Clean replacement
does not mean that lpsd silently deletes a store or creates new identities on
a decode failure. Reprovisioning is an explicit development/build operation.

lpsd keeps a per-principal credential generation in pending conversations.
Immediately before issuing an assertion it rechecks the principal is
enabled, the method remains permitted, the selected key is still enrolled,
and the generation has not changed. A changed generation terminates the
attempt; the client may start again. A positive candidate-key probe is
never cached as authorization for a later signature.

The assertion is the authentication decision's ordering point: removals
committed before it take effect for that attempt; removals committed after
it affect subsequent attempts. Already issued tokens and sessions are not
terminated by deleting a key. Revoking an existing session remains an
explicit session operation.

## Coordinated protocol replacement

`SshPublicKey` is credential type **2**; Password remains type 1. PGSS Logon
and PSI retain their existing header version **1**, magic, framing conventions,
and message-size ceilings. Each implements one codec for the revised layout.
There is no version negotiation, translation between old and new codecs, or
automatic fallback to the previous layout or a weaker credential.

This deliberately replaces unpublished contracts. The implementation updates
the existing enum-extension/version wording and message definitions together
with the code. authd, lpsd, login, GXWI, peinit, utilities, other active consumers,
and their dependency pins are rebuilt as needed for the revised shared types.
Old development binaries and stores are not a supported combination with the
replacement. Existing header-version and malformed-message checks remain;
they are not a compatibility mechanism for two layouts sharing version 1.

LogonStart contains `required_credential_type`, a `u8`: 0 leaves
the source's ordinary policy in control, 1 requires Password, and 2 requires
SshPublicKey. A nonzero value must appear in supported_credential_types.
PSI Authenticate carries the same requirement; its Assertion reports
`authenticated_credential_type` (0 means no credential). authd rejects a
result that fails a nonzero requirement. The SSH monitor selects 1 or 2
for its current method, so even an intentionally NoCredential principal
cannot produce an unearned successful SSH password/key authentication.
Rebuilt console and graphical clients retain their intended behavior by
explicitly declaring their capabilities and credential requirement.

The new fields follow the existing fields within their enclosing
length-framed structure. LogonStart appends required_credential_type, then
`has_ssh_binding` (u8, exactly 0 or 1), then the binding structure when
present. PSI Authenticate carries this extended LogonStart. Assertion
appends authenticated_credential_type. Prompt appends parameters. These
tails are mandatory even when their values are zero or empty;
truncation is an error, not permission to infer permissive defaults. Binding fields
are encoded in the order listed below: 16 raw connection-ID bytes, a byte
string session identifier, and a UTF-8 username. A binding is required for
type 2 and forbidden on attempts that do not advertise that type. Unknown
method values, invalid presence flags, and type-2 assertions in a
Password-only exchange are rejected.

PGSS and PSI share the revised credential bodies. The authority validates
and relays them without a legacy translation layer. The SSH
frontend advertises only the method of the current SSH authentication
attempt, so a separate password attempt remains possible only when policy
allows it.

A client advertising only Password is never sent type 2. A key-only account
reached through such a client is denied, not prompted for an invented
password and not granted without credentials. Identity, service-attestation,
and credential-change operations retain their intended behavior in the
coordinated build. This extension does not enable SSH key changes through
the password-change operation.

The new credential type is offered only to a client that declares it.
The authority also checks that the originator is allowed to provide SSH
transport bindings. Ordinary password collectors do not acquire that
authority by adding type 2 to their capability list.

## Binding the proof to a connection

Standard SSH signs the initial transport session identifier together with
the authentication request. It does not sign a fresh arbitrary challenge
invented by PGSS. The client-facing exchange remains RFC 4252 public-key
authentication; no Peios client extension is required.

For a key attempt, LogonStart includes a typed `SshTransportBinding`
structure. Its fields are a monitor-generated 16-byte connection ID, the
initial SSH session identifier (16–64 bytes), and the exact SSH username
(1–256 UTF-8 bytes). The username equals LogonStart's Username identifier
byte for byte. Other identifier types are rejected for this credential.
The SSH service is fixed to `ssh-connection` and the method to `publickey`
for this first implementation. The binding is copied into PSI Authenticate
from authd's validated conversation state, not from an Answer.

The monitor's connection ID is a correlation value, not proof or a bearer
capability. authd accepts binding claims only from a specifically authorized
service originator verified through its kernel socket-peer token. The implementation requires an unrestricted SYSTEM peer with the
enabled, non-deny-only service SID derived from the fixed service name
`sshd`, in addition to the ordinary originator/logon-type checks. This is
an SSH-specific gate, not a general service-group policy union. The network child and logged-on user must lack that service
authority and access to its PGSS descriptors.

The monitor obtains the initial session identifier from trusted key-exchange
state and pins it for the connection, including across rekeys. It does not
accept an arbitrary hash supplied through its authentication IPC. The
trusted monitor creates a fresh 16-byte server KEXINIT cookie. Before
signing the initial exchange hash it validates the bounded structured
transcript, requires that cookie and its own host public key, and recomputes
the SHA-256 or SHA-512 exchange hash. It supports ML-KEM/X25519,
sntrup761/X25519 and Curve25519 exchanges.
Simply remembering the first hash a child asks the host key to sign is not
accepted as proof of freshness against a compromised child.

This is an explicit trust boundary: lpsd verifies the signature, while the
SSH transport component vouches for the live connection. lpsd cannot
independently prove network freshness from a caller-supplied transcript.
A compromised authorized transport component is outside the guarantee;
an ordinary local process or compromised network parser is not.

All candidate offers on one SSH connection retain the same binding. The
monitor serializes attempts, fixes the target username for that connection,
and rejects username changes. Disconnect, monitor exit, loss of authd, or
successful authentication makes pending attempts unusable. A connection
receives at most one granted logon token. The monitor does not let a child
open an independent PGSS conversation using a previously accepted proof.

## Credential exchange

Prompt adds a length-framed `parameters` byte string, at most 4096
bytes. It is empty for Password. For SshPublicKey it contains a length-framed
structure containing a `disposition` byte: `0` initially, `1` for the previous
candidate being acceptable, and `2` for the previous candidate being
rejected. It describes only that candidate in that conversation; it never
asserts identity or grants access. There is one outstanding prompt, with a
fresh credential_ref for each round.

An SshPublicKey Answer.data contains a length-framed structure:

| Field | Encoding and limit |
|---|---|
| Operation | `u8`: 0 Candidate, 1 Proof |
| Signature algorithm | UTF-8 string, 1–64 bytes |
| Public key | Byte string, 1–8192 bytes |
| Signature | Byte string, 0–8192 bytes; empty exactly for Candidate |

The outer structure uses PGSS little-endian lengths. The public-key blob
and signature blob retain SSH's own encoding, including its big-endian
lengths. Unknown operations fail closed. Total answer
data remains below the existing 32768-byte ceiling; the parser additionally
rejects trailing fields outside this layout. No signed-data blob or
replacement session identifier is accepted in an answer.

For Candidate, lpsd checks whether that key and algorithm would be eligible
for the named principal and returns another SshPublicKey prompt with the
corresponding disposition. The monitor maps this to SSH's key-acceptable
reply or authentication failure. Unknown principals, disabled principals,
disallowed methods and unregistered keys all produce the same negative
result. Only one submission is in flight; the monitor consumes a disposition
before sending the next answer, abandons the PGSS exchange if the SSH client
switches methods, and never reports a probe response as logon success.
The positive result discloses eligibility of an already-presented
key, as standard SSH probing does; it does not enumerate keys.

For Proof, lpsd repeats eligibility checks and verifies the signature. A
client may send Proof without a preceding Candidate. Candidate success
never eliminates verification or the final account-state check. A bad
proof ends the PGSS attempt with a generic authentication failure. Trying
another key uses the next bounded SSH attempt; no proof is silently
reinterpreted as a different credential.

lpsd reconstructs the signed bytes exactly as RFC 4252 specifies: the
validated initial session identifier, message number 50, exact username,
`ssh-connection`, `publickey`, boolean true, algorithm and key blob. It
checks the algorithm agrees with the key and the signature's internal
algorithm identifier. There is no “verify these arbitrary bytes” API.
Case-insensitive principal lookup may resolve the username, but the signed
username is never case-normalized before signature verification.

When proof succeeds, lpsd emits the ordinary PSI assertion. The source
does not mint a token or choose additional privileges based on the key.
authd's AccessGranted is the only result permitting SSH authentication
success and session startup. Password and key are alternatives in the
initial policy model; partial success for multifactor authentication is
not implemented or advertised.

## Bounds, logging and failure behavior

One SSH connection has at most 16 public-key submissions total, counting
Candidate and Proof, and at most 6 failed signed/password attempts. Probes
consume the submission budget but do not by themselves trigger persistent
account lockout. The whole authentication exchange has a 120-second
deadline, without resets for probes or switching methods. Existing tighter
system limits still apply. Unknown users take the same bounded failure
path; no guarantee of exact constant-time public-key lookup is made.

The authority logs the originator, logon type and result; the source logs
the selected key fingerprint on success, and granted sessions carry their
principal/session identifiers.
Neither passwords, complete proofs nor private material appear in logs.
PGSS wire credentials use the existing self-wiping buffers. Parsed public
keys and SSH signatures are short-lived public cryptographic data; neither
is a password-equivalent secret or reusable bearer token.

Cryptographic verification failure, unsupported algorithm, revoked key,
disabled principal and disallowed method produce generic authentication
failure to the remote client. Detailed operational reasons are available
only through privileged local diagnostics. Invalid framing and state
transitions terminate the relevant conversation; they never become a
passwordless attempt.

## Qualification requirements

Required regression coverage includes:

- Successful key-only and password-only logons, and either-method policy;
  unsupported method and credential-free downgrade refusal.
- Rebuilt console/GXWI password logons and explicitly provisioned passwordless
  accounts, including fresh provisioning, restart, and failed store writes.
- Candidate acceptance without any assertion, direct Proof, multiple-key
  clients, budget exhaustion, cancellation, and identity-change refusal.
- Wrong signature, mismatched algorithm, wrong username/service/key,
  malformed nested lengths, unsupported versions, and cross-protocol input.
- Key removal, policy change and account disablement between Candidate and
  Proof and immediately before assertion; deletion of the last key.
- Captured proof replay on another SSH connection, an ordinary local PGSS
  connection, a new monitor, and after authd restart. Include a hostile
  network child proposing an old key-exchange hash, not just an honest
  client connecting twice.
- No PGSS or monitor descriptors, originator service authority, or elevated
  launch privileges inherited by the principal's shell.
- The final shell's actual primary token carries the intended principal,
  logon session, groups and policy, verified against kernel state.

## Service operation

The package `dev.peios.openssh` provides the Peios OpenSSH server and ordinary
SSH command-line tools. Its source repository owns the port and Pekit recipe;
there are no downstream source patches in the package catalogue.

All SSH logons use RemoteInteractive, including commands without a PTY and
SFTP. Password authentication requires an actual password; an intentionally
NoCredential account cannot log in through SSH. TCP, Unix-socket, agent,
X11 and tunnel forwarding are disabled in this first port.

The `sshd-service.reg` and `sshd-network.reg` vendor seeds are separate image
opt-ins. The service runs as SYSTEM with only SeChangeNotifyPrivilege,
SeAssignPrimaryTokenPrivilege and SeTcbPrivilege. The network seed permits
inbound TCP 22 and reserves that port for the sshd service SID. The network
child loses its privileges and service-group authority, receives an Everyone
restricting SID, and retains upstream chroot and seccomp protection. The
session child installs the granted principal token before accepting the
post-authentication network state.

Defaults are `/usr/etc/ssh/sshd_config`; administrator overrides may use
`/lcl/etc/ssh/sshd_config`. The service generates an Ed25519 host key on first
start in protected persistent `/var/state/sshd`, validates and reuses it on
subsequent starts, and fails on an invalid existing key. It never rotates a
key automatically. Client private keys remain with the client.

Provision a key-only account while disabled to avoid a temporary
NoCredential window:

```sh
lps add alice --no-password --disabled
lps key add alice /path/to/alice.pub laptop
lps policy alice key
lps enable alice
lps key list alice
```

Use `lps policy alice either` to allow either an enrolled key or an existing
password. Key removal uses the record ID printed by `lps key list`:
`lps key remove alice RECORD_ID`. Changing material does not change policy.

## References

- [RFC 4252, section 7](https://www.rfc-editor.org/rfc/rfc4252.html#section-7):
  candidate-key queries, direct signed requests, and exact signed fields.
- [RFC 8332](https://www.rfc-editor.org/rfc/rfc8332.html): RSA SHA-2 signature
  algorithm names and reuse of the RSA public-key encoding.
- [OpenSSH Portable monitor](https://github.com/openssh/openssh-portable/blob/master/monitor.c):
  upstream privilege-separation integration reference; it does not by
  itself establish Peios originator authorization or this contract's
  trusted-transport freshness requirement.
