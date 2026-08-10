---
title: Account Administration
---

Account administration is **source-shaped** and therefore goes directly
to a source (§2.2), except for the source-transparent self-service verbs
that the broker forwards. For lpsd, administration is served on
`/run/lpsd.sock` (§6.1).

## Administration operations

lpsd's administration interface MUST provide at least:

- **CreateUser** — allocate a RID from `rid_counter`, assign an
  `object_guid` and POSIX projection, set the `BUILTIN\Users` primary
  group and membership, write the user record (§3.2).
- **SetPassword** (administrative reset) — set the `password` factor
  without the old password, subject to the password policy (§3.4); gated
  by the Reset Password control-access right (below).
- **CreateGroup**, **AddMember**, **RemoveMember** — manage groups and
  membership (§3.2).
- **EnableAccount** / **DisableAccount** — toggle `account_flags`.

Administration clients route between sources by namespace via a shared
client library (§2.2); a domain source serves the corresponding directory
operations, which need not match lpsd's shape.

## Authorization: principal security descriptors

Account administration is **not** gated by a dedicated privilege. Every
lpsd principal — each user, each group — and the **domain object** itself
(§3.1) is a securable object carrying a KACS **security descriptor** (SD;
PSD-004 §3, `ACL_REVISION_DS`). An administration request is authorized by
a KACS **AccessCheck** (`kacs_access_check`, or `kacs_access_check_list`
for the per-property case — PSD-004 §10) of the **caller's peer token**
(§6.2) against the target object's SD for the operation's required access.
lpsd holds no `SeTcbPrivilege`; it evaluates the check via the kernel
primitive and honours the verdict. There is no "account-admin privilege"
and no built-in group is hard-coded into the gate — authority is whatever
the object SDs grant, exactly as for any other securable object.

This is the Windows/AD authorization model, **isomorphic** to it but
realized over lpsd's flat store: principals are securable objects, access
is an object-ACE AccessCheck, and the rights are AD's own — the
control-access rights **Reset Password** and **Change Password**, the
per-attribute **property-set** rights, and the standard `DELETE` /
`WRITE_DAC` / `WRITE_OWNER` / `READ_CONTROL` rights. The GUIDs that name
these rights are **AD's well-known GUIDs**, adopted verbatim for parity
(catalogued in §9), so an operator's AD mental model, a future adpsd, and
lpsd all speak one access-rights vocabulary.

### The domain object is the container

`CreateUser` and `CreateGroup` cannot be gated by the new principal's own
SD — it does not exist yet — so they are gated by **create-child** access
on the **domain object's** SD, class-scoped by an object-ACE
`ObjectType`/`InheritedObjectType` GUID to the user vs group class (§9).
Enumeration is gated by **list-contents** on the domain object. The domain
object's SD also carries the **inheritable** object-ACEs that seed every
new principal's SD at creation (Creator Owner/Group placeholders resolved
per PSD-004 §2). Because there is exactly one container, this yields
**domain-wide** delegation — e.g. an ACE granting an operator group
Reset-Password on all user-class children. There is no finer,
sub-container scoping, and there is not meant to be: lpsd is a flat store
by design (§3 — no DIT, no organisational units). Hierarchical
(OU-scoped) delegation is a property of a *directory* source — it would
live in adpsd's AD backend when domain support lands (§8) — and is not an
lpsd concept.

The built-in principals (Administrator, Guest, and the `S-1-5-32` alias
groups) live in this **same single container** — lpsd does not segregate
them into a separate container — but each carries its own locked-down
default SD (§9). Shielding admin and built-in principals from a *broad*
delegation ACE placed on the container is the deferred **protected-accounts
guardrail** (§8), which keys protection on Administrators **membership**
rather than on container placement — because a regular user added to
Administrators is exposed by exactly the same broad ACE and a separate
container would not cover them.

### Verb → required access

| Verb | Target object | Required access |
|---|---|---|
| `CreateUser` / `CreateGroup` | domain object | create-child, class-scoped to user/group (§9) |
| (enumerate) | domain object | list-contents |
| `SetPassword` (reset) | target principal | **Reset Password** control-access right (§9) |
| ChangePassword (self-service) | caller's own principal | **Change Password** control-access right — held by a principal on itself — **plus** knowledge of the old password (§7.2 above, §6.4) |
| `AddMember` / `RemoveMember` | target **group** | write the **Membership** property (§9) |
| `EnableAccount` / `DisableAccount` | target principal | write the **Account-Restrictions** property (§9) |
| (delete) | target principal | `DELETE` |

The issue that motivated this — password reset versus self-service change
— now falls out of the model as two distinct AD control-access rights on
the same object, rather than two ad-hoc gates: a caller with **Reset
Password** on the target resets without the old password; a principal has
**Change Password** on *itself*, additionally gated by old-password
knowledge so the right alone does not permit a credential-free change.

## ChangePassword (self-service, forwarded)

ChangePassword is source-transparent and is forwarded by authd (§2.2,
§6.3). authd routes it by the principal's namespace exactly as for a
Logon and forwards it, unmodified, to the source's socket as the
source-side `CHANGE_PASSWORD` (§6.4 type 17). lpsd's self-service
ChangePassword verb MUST be authorized by **knowledge of the old
password**: the request carries the old and new passwords, and lpsd
verifies the old before applying the new (open to any caller, consistent
with the knowledge-gates model of §6.3). The authorization is knowledge,
not identity — which is what lets the request be forwarded, since the
source captures authd (not the original caller) as its peer and so cannot
gate on the caller's privilege.

Because that old-password check is a full credential verification, it is
subject to **exactly the same guardrails as a logon**: the source runs the
lockout accounting and account-state gating of §3.4 and the constant-time
comparison, dummy-verifier, and uniform-failure enumeration resistance of
§3.3 (a locked or disabled account is refused, an expired one is not since
the change clears it), and authd counts the request against the same
throttle budgets as `LOGON` (§6.3). Otherwise ChangePassword would be an
unthrottled, lockout-free credential oracle against the same verifier
(§3.3).

This verb serves both ordinary password changes and the
`must_change_password` flow (§5.1): a TCB login frontend relays the
user's old and new passwords after a `must_change_password` result, and
lpsd's verification of the old password is the authorization — no special
privilege is required.

**Administrative reset** — changing a password *without* the old one — is
a distinct, source-shaped operation: it is `SetPassword` above, sent
**directly** to the admin socket and gated by the **Reset Password**
control-access right on the target principal's SD, checked against the
caller's own peer token. It is never forwarded through authd, precisely
because an SD AccessCheck must run against the caller's identity, which a
forward replaces with authd's.

## Propagation

Administrative changes take effect at the principal's **next logon**: a
token reflects logon-time identity and is immutable (PSD-004). Live
sessions are unaffected until re-logon or forced logout (§6.3). authd
and the administration interface therefore need no coupling for
propagation.
