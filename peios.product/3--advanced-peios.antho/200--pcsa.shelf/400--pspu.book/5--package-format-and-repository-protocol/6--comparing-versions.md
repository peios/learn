---
title: Comparing Versions
description: The three-stage comparison that decides which of two versions is newer, including pre-release segments and their rank.
---

Two version strings are compared in three stages:

1. Compare epochs as integers. If they differ, the higher epoch is
   greater.
2. If equal, compare upstream versions by the algorithm below.
3. If equal, compare peios revisions as integers. The higher revision is
   greater.
4. If all three are equal, the versions are equal.

## Tokenising the upstream version

A tokeniser walks the upstream string left to right and emits segments:

1. The non-alphanumeric characters `.`, `+`, `-`, and `~` are separators
   and belong to no segment.
2. A maximal run of digits forms a **numeric** segment.
3. A maximal run of letters forms an **alphabetic** segment.
4. A transition between a digit and a letter ends the current segment
   and begins a new one.

## Pre-release segments

A segment is a **pre-release segment** if it falls at or after the
earlier of:

- the first `~` separator — the tilde and every segment following it; or
- the first **recognised pre-release token**: a segment whose token
  carries a rank of 0 to 4 in the table below, that segment and every
  segment following it.

Once the pre-release tail begins it extends to the end of the upstream
version: every later segment is a pre-release segment, whatever the
separators between them. A `-` separator is an ordinary separator; it is
not itself a pre-release marker.

> [!NOTE]
> In `1.0.0-rc.1`, `rc` is recognised at rank 4, so `rc` and the
> following `1` are pre-release. In `16beta1`, `beta` is recognised at
> rank 2, so `beta` and `1` are pre-release with no separator involved.
> In `1.0-foo`, `foo` is alphabetic but not recognised: it is an
> ordinary rank-5 segment, and the `-` before it begins nothing.

| Upstream | Segments |
|---|---|
| `1.26.2` | `1`, `26`, `2` |
| `1.0.0-rc.1` | `1`, `0`, `0`, `rc` (pre), `1` (pre) |
| `1.0~rc1` | `1`, `0`, `rc` (pre), `1` (pre) |
| `16beta1` | `16`, `beta` (pre), `1` (pre) |

## Pre-release rank

| Token | Rank |
|---|---|
| `dev` | 0 |
| `alpha` | 1 |
| `a` | 1 |
| `beta` | 2 |
| `b` | 2 |
| `pre` | 3 |
| `rc` | 4 |
| any other alphabetic token | 5 |

Rank 0 sorts lowest. Rank lookup MUST be case-insensitive: `Alpha`,
`ALPHA`, and `alpha` all carry rank 1.

## Comparing two segments

1. **Both numeric** — compare as integers. Leading zeros are
   insignificant.
2. **Both alphabetic** — compare by pre-release rank. When the ranks are
   equal:
   - at a rank of 0 to 4, the segments are **equivalent**. The table
     assigns several tokens to one rank as aliases, so two segments at
     the same recognised rank sort equal whichever alias appears.
   - at rank 5, the segments tiebreak by ASCII byte order against other
     rank-5 tokens.
3. **One numeric, one alphabetic** — if the alphabetic segment is a
   pre-release segment, it is the lesser. If it is not, the numeric
   segment is the lesser.

> [!NOTE]
> ```
> 1.0~alpha-1 == 1.0~a-1       # both rank 1
> 1.0~beta-1  == 1.0~b-1       # both rank 2
> 1.0~Alpha-1 == 1.0~ALPHA-1   # case-insensitive recognition
> 1.0-foo-1   <  1.0-zzz-1     # rank-5 lexical tiebreak
> ```
> Two upstream versions that differ only in which alias they use are
> equal. A repository publishing both forms produces archive entries at
> the same logical version; the active index may carry either. A
> producer SHOULD pick one canonical form — conventionally the long
> token, `alpha` and `beta` — and keep to it.

## Unequal lengths

When the segments of one version run out and every common segment
compared equal, the next segment of the longer sequence decides:

| Next segment in the longer | Result |
|---|---|
| numeric | the shorter is less |
| alphabetic, pre-release | the shorter is **greater** |
| alphabetic, not pre-release | the shorter is less |

## Worked examples

| A | B | Result | Why |
|---|---|---|---|
| `1.0` | `1.0` | A = B | identical |
| `1.0` | `2.0` | A < B | numeric segment differs |
| `1.10` | `1.9` | A > B | numeric, not lexical |
| `1.0` | `1.0.1` | A < B | longer continues numerically |
| `1.0` | `1.0-rc.1` | A > B | longer continues with a pre-release |
| `1.0-rc.1` | `1.0-rc.2` | A < B | numeric segment within the tail |
| `1.0-alpha` | `1.0-beta` | A < B | rank 1 < rank 2 |
| `1.0-rc` | `1.0-pre` | A > B | rank 4 > rank 3 |
| `1.0a1` | `1.0a2` | A < B | numeric within a concatenated tail |
| `1.0a1` | `1.0b1` | A < B | rank 1 < rank 2 |
| `1.0~rc1` | `1.0` | A < B | the tilde forces a pre-release |
| `0:1.0` | `1:0.5` | A < B | epoch dominates |
| `1.0-1` | `1.0-2` | A < B | peios revision differs |
| `1.0-foo-1` | `1.0-1` | A > B | `foo` is rank 5, sorting after a number |
