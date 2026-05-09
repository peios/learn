---
title: Versioning
---

Each package has a version string that uniquely identifies a
build of that package. Version strings have a defined structure
and a defined comparison order so that "newer" and "older" are
unambiguous.

## Structure

A version string has the form:

```
[<epoch>:]<upstream>-<peios_revision>
```

The components are:

- **Epoch**: An OPTIONAL non-negative integer, separated from
  the rest of the version by a colon. If absent, the epoch is
  treated as 0.
- **Upstream**: The version string assigned by the upstream
  project, or for Peios-native software, the version assigned
  by Peios as the vendor.
- **Peios revision**: A REQUIRED positive integer
  identifying the build of this upstream version produced by
  the Peios project.

Examples:

```
1.26.2-3            upstream 1.26.2, peios revision 3
1.26.2-rc.1-1       upstream 1.26.2-rc.1, peios revision 1
2:0.5.0-1           epoch 2, upstream 0.5.0, peios revision 1
0.22-1              upstream 0.22, peios revision 1 (peios-native)
```

## Epoch

The epoch is a non-negative integer. It MUST be encoded as
ASCII decimal digits with no leading zeros, except that the
value zero is encoded as the single digit `0`.

The epoch separator is a single colon (`:`).

Epoch is used solely to override the natural ordering of
upstream version strings when an upstream version regression
makes a later release compare as "older" than an earlier one.

> [!INFORMATIVE]
> Example: an upstream project releases v2.0, then later
> abandons that line and releases v0.5 as their new "stable"
> branch. Without epoch, v0.5 compares as older than v2.0,
> which would prevent users on v2.0 from upgrading. Bumping
> the epoch to 1 expresses "v0.5 in this epoch is newer than
> anything in epoch 0".

Bumping the epoch SHOULD be a deliberate, documented
decision. Routine version updates MUST NOT bump the epoch.

## Upstream version

The upstream version is the portion of the version string
between the optional epoch separator and the final hyphen
that precedes the peios revision.

The upstream version MUST consist of ASCII characters from
the following set:

- Lowercase and uppercase letters `a` through `z`, `A`
  through `Z`
- Digits `0` through `9`
- Period `.`
- Plus sign `+`
- Hyphen `-`
- Tilde `~`

The upstream version MUST start with a digit or a letter.

The upstream version MUST NOT contain whitespace or any
character outside the set above.

> [!INFORMATIVE]
> The character set is permissive to accommodate the diverse
> ways upstream projects format their versions: numeric
> (`1.26.2`), pre-release with hyphen (`1.0.0-rc.1`),
> pre-release with concatenation (`16beta1`), build metadata
> (`1.0+build.42`), and tilde-separated pre-release
> (`1.0~rc.1`).

## Peios revision

The peios revision is a positive integer. It MUST be encoded
as ASCII decimal digits with no leading zeros.

The revision is incremented when the Peios project produces a
new build of the same upstream version. Reasons include
security-patch backporting, build configuration changes,
dependency updates, and packaging fixes.

The first revision of any upstream version MUST be 1. Revision
0 is reserved and MUST NOT appear in published packages.

## Parsing

A version string is parsed as follows:

1. If the string contains a colon, split at the first colon.
   The portion before the colon is the epoch; the portion
   after is the remainder.
2. Otherwise, the epoch is 0 and the remainder is the entire
   string.
3. Split the remainder at the last hyphen. The portion after
   the last hyphen is the peios revision; the portion before
   is the upstream version.
4. The peios revision MUST parse as a positive integer.
5. The upstream version MUST conform to the character set and
   structural constraints above.

A version string that does not parse is INVALID. An
implementation MUST reject invalid version strings.

## Comparison

Two version strings A and B are compared as follows:

1. Compare epochs as integers. If they differ, the version
   with the higher epoch is greater.
2. If equal, compare upstream versions using the upstream
   comparison algorithm (§2.2.7).
3. If equal, compare peios revisions as integers. The version
   with the higher revision is greater.
4. If all three are equal, the versions are equal.

## Upstream comparison

Upstream version strings are compared by tokenisation and
segment-wise comparison.

### Tokenisation

A tokeniser walks the upstream string left to right and
emits a sequence of segments. Segments are emitted as
follows:

1. Non-alphanumeric characters (`.`, `+`, `-`, `~`) are
   separators and are not part of any segment.
2. A maximal run of digits forms a numeric segment.
3. A maximal run of letters forms an alphabetic segment.
4. A transition between a digit and a letter ends the
   current segment and begins a new one.

The tilde character (`~`) is a special separator: any segment
that immediately follows a tilde is marked as a pre-release
segment regardless of its content.

> [!INFORMATIVE]
> Example tokenisations:
>
> | Upstream | Segments |
> |---|---|
> | `1.26.2` | `1`, `26`, `2` |
> | `1.0.0-rc.1` | `1`, `0`, `0`, `rc` (pre), `1` (pre) |
> | `1.0~rc1` | `1`, `0`, `rc` (pre), `1` (pre) |
> | `16beta1` | `16`, `beta` (pre), `1` (pre) |
>
> Segments after a `~` and segments after a `-` followed by
> an alphabetic segment are both treated as pre-release
> segments. See §2.2.7.3 for the precise rule.

### Segment comparison

Two segments are compared as follows:

1. If both segments are numeric: compare as integers. Leading
   zeros are insignificant.
2. If both segments are alphabetic: compare by pre-release
   rank (defined below). When both ranks are equal:
   - If the rank is 0–4 (a recognised pre-release rank), the
     segments are *equivalent*. The rank table assigns multiple
     tokens to a single rank as aliases (`alpha` and `a` both
     at rank 1, `beta` and `b` both at rank 2); two segments at
     the same recognised rank sort equal regardless of which
     alias appears in the version string.
   - If the rank is 5 (no recognised pre-release token), the
     segments tiebreak by ASCII byte order amongst other
     rank-5 tokens.
3. If one segment is numeric and the other is alphabetic:
   - If the alphabetic segment is a pre-release segment, the
     alphabetic segment is less than the numeric segment.
   - If the alphabetic segment is not a pre-release segment,
     the numeric segment is less than the alphabetic segment.

The pre-release rank assigns the following well-known tokens
explicit ordinal values (lowest to highest):

| Token | Rank |
|---|---|
| `dev` | 0 |
| `alpha` | 1 |
| `a` | 1 |
| `beta` | 2 |
| `b` | 2 |
| `pre` | 3 |
| `rc` | 4 |

Any other alphabetic token has rank 5 and is compared
lexically against other rank-5 tokens.

Comparison is case-insensitive for pre-release rank lookup
(`Alpha` and `ALPHA` both rank 1).

> [!INFORMATIVE]
> Examples of the aliasing rule:
>
> ```
> 1.0~alpha-1 == 1.0~a-1       # both rank 1
> 1.0~beta-1  == 1.0~b-1       # both rank 2
> 1.0~Alpha-1 == 1.0~ALPHA-1   # case-insensitive recognition (both rank 1)
> 1.0-foo-1   <  1.0-zzz-1     # rank-5 lex tiebreak
> ```
>
> Two upstream versions that differ only in which alias they
> use for a pre-release token are equivalent. A repository
> publishing both forms produces archive entries with the
> same logical version; the active index is allowed to pick
> any one of them, but build pipelines SHOULD pick a
> canonical form (typically the long token: `alpha`, `beta`)
> and stick with it to avoid confusing operators.

### Implicit pre-release detection

A `-` separator preceding a non-pre-release alphabetic segment
within the upstream version is treated as if it were a `~`
separator: the alphabetic segment and all subsequent segments
in the same hyphen-delimited group are marked as pre-release.

> [!INFORMATIVE]
> Example: in upstream version `1.0.0-rc.1`, the segment
> `rc` after `-` is alphabetic and matches a pre-release
> token (rank 4), so the `-` is treated as a pre-release
> marker. The `rc` and `1` segments are pre-release.
>
> In upstream version `1.0-foo`, `foo` is alphabetic but is
> not a recognised pre-release token. The `-` is therefore
> not treated as a pre-release marker, and `foo` is a
> regular alphabetic segment with rank 5 (lexical).
> Architecture suffixes do not appear in upstream version
> strings; architecture is a separate identifier (§2.3).

### End-of-string handling

When one segment sequence is shorter than the other:

1. If the next segment in the longer sequence is numeric, the
   shorter sequence is less than the longer sequence.
2. If the next segment in the longer sequence is alphabetic
   and a pre-release segment, the shorter sequence is greater
   than the longer sequence.
3. If the next segment in the longer sequence is alphabetic
   and not a pre-release segment, the shorter sequence is
   less than the longer sequence.

> [!INFORMATIVE]
> Examples:
>
> | A | B | Result | Rule |
> |---|---|---|---|
> | `1.0` | `1.0.1` | A < B | numeric extension |
> | `1.0` | `1.0-rc.1` | A > B | pre-release suffix |
> | `1.0` | `1.0.alpha` | A > B | pre-release alphabetic |
> | `1.0` | `1.0a` | A > B | pre-release token |

## Constraints

Version constraints (used by dependencies, see §4.1) use
standard relational operators:

| Operator | Meaning |
|---|---|
| `=` | Exactly equal |
| `>` | Strictly greater than |
| `>=` | Greater than or equal |
| `<` | Strictly less than |
| `<=` | Less than or equal |
| `!=` | Not equal |

Multiple constraints on the same dependency are combined with
logical AND. Comma is the AND separator.

Examples:

```
libssl >= 3.0
libssl >= 3.0, < 4.0
nginx = 1.26.2-3
```

A constraint without an operator (a bare version) is
equivalent to `=`.

## Stability across versions

A `final` version of this specification freezes the version
comparison algorithm. An implementation conforming to this
specification version MUST produce identical comparison
results to any other conforming implementation for any pair
of valid version strings.
