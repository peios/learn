---
title: Agents
type: reference
description: A pane can hold a chat with an agent such as Claude Code instead of a shell. How to open one, how typing and the agent's questions work, what the chat shows, which agent it talks to and what that costs, and what survives closing the window or upgrading.
related:
  - clackatoo/reference/window
  - clackatoo/reference/cli
---

A pane can hold a chat with an agent, such as Claude Code, instead of a shell. You type a message in the box along the bottom, the agent answers above it, and it works on the files in the pane's directory as it would in its own program.

Your messages are bubbles on the right. The agent's answers run the width of a column down the middle of the pane, with Markdown laid out as it's meant to look: headings, lists, quotes, links, and code in the terminal's font on a background of its own.

## Opening a chat

| | Does |
|---|---|
| Ctrl+B `a` | Opens a chat to the right of the focused pane. |
| `:Agent` | Opens a chat in a new tab. |
| `:\|Agent`, `:-Agent`… | Opens a chat beside the focused pane, as `:|Terminal` opens a terminal. |

A chat works in the directory a new terminal would start in: the one the pane it splits is in, or for a new tab, the one the workspace's focused pane is in. That's where the agent reads and changes files, and runs its commands.

Like any new pane, a chat opens in normal mode: `i` starts typing into it. The first chat starts the agent, which takes a second or two. Until then the chat says it's starting, and a message sent meanwhile waits and goes when it can.

## Typing

In insert mode, what you type goes in the box at the bottom.

| Key | Does |
|---|---|
| Enter | Sends the message. |
| Shift+Enter | Starts a new line in the message. |
| Ctrl+C | Copies what's selected in the message, or else, while the agent answers, asks it to stop. |
| Backspace, Delete | Delete a character, or with Ctrl, a word. |
| Left, Right | Move by a character, or with Ctrl, a word. With Shift, they select. |
| Up, Down, Home, End | Move by a line, or to its start or end. With Shift, they select. |
| Ctrl+A | Selects the whole message. |
| Shift+Tab | Moves the agent on to its next mode. |
| Esc | Normal mode. There's no program in a chat to need Esc. |

Clicking in the box puts the cursor there, dragging selects, and a double or triple click selects a word or a line. A paste goes into the message whole, lines and all, without sending it. Text can be typed through an input method: what's being composed shows in the box, at the cursor, until it's committed.

A message beginning with `/` goes to the agent as typed, which is how agents take their own commands, such as Claude Code's `/compact`.

One message is answered at a time. While the agent answers, the button in the box's corner is a stop button, and Enter keeps what you typed until it's done. Clicking the button with nothing being answered sends the message, as Enter does.

What you've typed but not sent belongs to the window: another window, or this one after it closes, starts with an empty box.

## The agent's settings

Along the bottom of the box are the agent's settings for the chat, as the agent offers them. For Claude Code:

- **On the left, its mode:** how much it does without asking. Manual asks before every change, Accept edits makes edits without asking, Plan plans before it acts, and Auto lets Claude decide what needs asking about. A new chat starts in Auto.
- **On the right, its model and effort**, such as `Sonnet 5.5 · High`.
- **Beside them, how much of the model's context the chat fills**, such as `38k / 200k`.

Click a setting to open its menu, above the box. Up and Down move through it, Enter or a click picks, and Esc or a click elsewhere closes it. Shift+Tab steps through the modes without opening the menu.

A chat keeps the settings you pick. If the agent stops, or the daemon is [upgraded](~clackatoo/reference/cli#upgrade), the chat asks for them again as its session reopens.

## Normal mode

In normal mode, keys move the view instead:

| Key | Does |
|---|---|
| `j` `k`, Down Up | A line down or up. |
| Ctrl+D Ctrl+U, Page Down Page Up | Half a view down or up. |
| `gg` `G` | The start or end of the chat. |
| `i`, `a`, Enter | Back to insert mode. |

The mouse wheel scrolls in either mode. While you're at the end, the view follows the answer as it grows. Scrolled up, it stays put, and the bottom bar says so.

## What the chat shows

Below each message you send, what the agent did with it, in order:

- its words
- its thinking, if it shows any, quieter and slanted
- each tool it uses, on a line of its own: `○` while it runs, then `✓` once it has finished, or `✗` if it failed

While the agent works, the turn ends with `Working…`. A turn the agent didn't finish says why: `Stopped.`, or what went wrong. The tab is named after the title the agent gives the conversation.

### When the agent asks

In Manual mode, before it does anything that changes something, such as writing a file or running a command that isn't only reading, the agent asks. Other modes ask about less, and Auto leaves it to Claude. Its question takes the box's place, with an answer on each button: the first way to say yes in the accent colour, and the ways to say no quieter.

Click an answer, or press its number. Esc says no. Ctrl+C says no and stops the answer.

What it asks about follows the agent's own settings. Claude Code reads its usual settings files, so commands you've allowed in Claude Code are allowed here too.

## Which agent

Chats talk to Claude Code. clackatoo speaks ACP, the [Agent Client Protocol](https://agentclientprotocol.com), which Claude Code doesn't speak itself, so the daemon runs Claude Code's ACP adapter, `@agentclientprotocol/claude-agent-acp`, with `npx`. That needs Node.js, and the first chat downloads the adapter. The adapter runs a copy of Claude Code that comes with it, at a version tried with clackatoo, not the `claude` you may have installed.

It uses the account Claude Code is logged in to. Log in once with `claude` in a terminal, and every chat uses that login. With a Claude subscription, chats count towards the subscription's limits, as Claude Code does.

To talk to another agent that speaks ACP, set `CLACKATOO_AGENT` for the daemon to its command, split at spaces. The daemon reads it when it starts.

One agent process serves every chat. Claude Code's adapter starts a Claude Code process for each chat as well, of about 250 MB, and the adapter itself takes about 115 MB. Closing a chat's pane ends its process, and closing the last chat stops the agent.

## What lasts

The daemon keeps chats, as it keeps terminals. Closing the window closes nothing: a chat keeps answering, and the next window shows it.

[Upgrading](~clackatoo/reference/cli#upgrade) the daemon keeps each chat's conversation, but stops the agent. An answer that was under way is cut off, and the turn says so. The next message starts the agent again and carries on the same conversation. A chat from a build before chats were kept as turns comes through as one block of its text.

If the agent stops on its own, the chat says so, and the next message starts it again, carrying on the same conversation.

When the daemon itself stops, its chats go with its terminals.

`clackatoo capture` prints a chat as text: each message after a `>`, and what the agent said.

## Not yet

- Text in the conversation can't be selected or copied yet: only the message being typed.
- The thinking and tool calls of a turn don't fold away under a "Worked for…" line yet.
- Commands the agent runs show only as a line with their title. They'll run in terminals beside the chat, which you can watch and take over.
- Claude's 5-hour and weekly usage limits aren't shown.
- Diffs of the files the agent changes aren't shown.
- Images can't be pasted into a message.
- `/` commands aren't listed or completed as you type them.
