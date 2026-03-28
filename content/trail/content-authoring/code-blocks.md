---
title: Code Blocks
type: concept
order: 70
description: Trail highlights code blocks at build time using Chroma with the Dracula theme. Every code block has a copy button.
---

Code blocks in Trail are highlighted at build time. There is no client-side syntax highlighting library loaded at runtime.

## Basic syntax

Use standard Markdown fenced code blocks with a language tag:

````markdown
```go
func main() {
    fmt.Println("hello")
}
```
````

The language tag after the opening fence determines which syntax rules are applied.

## Syntax highlighting

Trail uses [Goldmark](https://github.com/yuin/goldmark) with the [goldmark-highlighting](https://github.com/yuin/goldmark-highlighting) extension, which is powered by [Chroma](https://github.com/alecthomas/chroma). Highlighting happens at build time and produces inline `<span>` elements with color styles.

The theme is **Dracula** -- a dark background with colored syntax tokens. The code block background is always dark (`#282a36`) regardless of whether the page is in light or dark mode.

## Supported languages

Chroma supports hundreds of languages. Common ones used in documentation:

| Language tag | Language |
|---|---|
| `go` | Go |
| `rust` | Rust |
| `python` | Python |
| `javascript` or `js` | JavaScript |
| `typescript` or `ts` | TypeScript |
| `bash` or `sh` | Shell/Bash |
| `toml` | TOML |
| `yaml` | YAML |
| `json` | JSON |
| `sql` | SQL |
| `html` | HTML |
| `css` | CSS |
| `c` | C |
| `markdown` or `md` | Markdown |
| `diff` | Diff |
| `lua` | Lua |

If no language tag is provided, the code block is rendered without highlighting but retains the Dracula background.

See the [Chroma language list](https://github.com/alecthomas/chroma#supported-languages) for the complete set.

## Copy button

Every code block automatically receives a "Copy" button. The button appears in the top-right corner when the reader hovers over the code block. Clicking it copies the code text (without any HTML formatting) to the clipboard. The button text changes to "Copied!" for 1.5 seconds as confirmation.

The copy button works on all code blocks, including those inside tab groups.

## Inline code

Inline code uses single backticks and is styled differently from code blocks:

```markdown
Use the `trail build` command to generate the site.
```

Inline code renders with a light gray background in light mode and a dark gray background in dark mode. It does not receive syntax highlighting or a copy button.

## Code blocks in tab groups

Code blocks inside tab groups render flush against the tab container. The code block's top corners are not rounded, and there is no margin, creating a seamless appearance where the tab buttons sit directly above the code.

This is useful for showing the same concept in multiple languages:

````markdown
<!-- tabs -->
<!-- tab:Go -->

```go
fmt.Println("hello")
```

<!-- tab:Python -->

```python
print("hello")
```

<!-- tab:Rust -->

```rust
println!("hello");
```

<!-- /tabs -->
````

## GFM extensions

Trail enables several Goldmark extensions that affect how content inside and around code blocks is processed:

| Extension | Effect |
|---|---|
| **Tables** | GFM table syntax with `|` pipes |
| **Strikethrough** | `~~text~~` renders as strikethrough |
| **Auto heading IDs** | Headings get `id` attributes automatically |
| **Unsafe HTML** | Raw HTML in Markdown is passed through (needed for tab groups and other features) |
