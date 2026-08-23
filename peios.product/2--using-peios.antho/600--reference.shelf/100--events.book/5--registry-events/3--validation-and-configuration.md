---
title: Validation and Configuration Failures
description: The two events LCS emits for malformed source data and invalid self-configuration — and why a first boot produces nineteen of them.
---

## LCS_SOURCE_VALIDATION_FAILURE

Fires when LCS rejects malformed source data.

Carries the source slot identifier, then — where each is known — the
hive name, the RSI request id, the operation code and the key GUID. The
last field, `validation_class`, names what was wrong.

There are **twelve** classes:

| Group | Classes |
|---|---|
| Name fields | `malformed_layer_name`, `malformed_key_name`, `malformed_value_name` |
| Structural | `malformed_response_payload`, `malformed_key_metadata`, `malformed_value_payload`, `malformed_delete_layer_orphan_list` |
| Descriptors | `malformed_security_descriptor`, `malformed_layer_metadata_security_descriptor` |
| Sequencing | `future_sequence_number`, `duplicate_winning_sequence_tie` |
| Protocol | `unknown_rsi_status_code` |

The three name classes are field-specific — layer-name fields, key
component or child-name fields, and value-name fields respectively.

The structural classes cover a response whose operation-specific payload
has the wrong shape or trailing bytes; a lookup or enumeration whose
metadata block is incomplete, duplicated, unreferenced or nil; a value
payload with an invalid type, a tombstone/data mismatch or oversized
data; and an invalid orphan GUID array from `RSI_DELETE_LAYER`.

## LCS_SELF_CONFIG_INVALID

Fires when LCS rejects an invalid self-configuration value.

Carries the parent path and value name of the offending parameter, the
expected type and numeric range, what was actually received — one of
`missing`, `wrong_type` or `dword_out_of_range`, with the actual type or
value where applicable — and the value LCS retained instead.

### Expect nineteen of these on a first boot

Because `missing` counts as invalid, a first boot before seed restore
emits one event **per parameter on each refresh**: nineteen events
against an empty `Registry\` key.

That is correct and expected, and it is a noticeable share of the boot
audit stream. A consumer alerting on validation failures needs to know
it, or every fresh machine looks like it is failing.
