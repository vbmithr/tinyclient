# Chatd IPC type catalogue

Companion to [the IPC specification](chatd-ipc.md). Extracted from all 94
top-level serializable protocol types at upstream commit `7b98c4c`, including
68 request variants, 30 response variants and 19 change variants. Names in
backticks are symbolic types, not a requirement to use Rust. This catalogue
also includes media-helper types; only `Request` is accepted on `chat.sock`.

## Reading the catalogue

`uintN` and `intN` are JSON integers of the stated width; `floatN` is a finite
JSON number. `list<T>` is an array; `tuple(A,B)` is a fixed-length JSON array.
`nullable<T>` accepts null or the referenced value. `Box<T>` has no wire effect.
`usize`, where present, is bounded by the reference platform; do not infer a
portable wire width from it. Object field order is insignificant.

An **error** in the Missing field column means the reference decoder requires
the field. A field that accepts null is not necessarily omitted by the encoder.
Type defaults, custom defaults and omission predicates are explained in the
specification. Each type links to the exact source; descriptive source comments
are included, but runtime limits and side effects come from the specification.

The following predicate names preserve the reference implementation terminology:
`Option::is_none` means null/absent; `Vec::is_empty` means `[]`;
`String::is_empty` means `""`; `is_false`/`Not::not` mean false; `is_true` means
true; `is_zero`/`is_zero64` mean zero. Enum predicates such as `is_sent`,
`is_normal`, `is_section`, `is_main` and `is_any` select their named default
variant. `Capabilities::is_none` and `Keychain::is_settled` are defined in the
linked source and covered by the defaults section of the specification.

## Request

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

Internally tagged object: discriminator `op`.

### ping

Discriminator: `"op": "ping"`.

No payload fields.

### status

Discriminator: `"op": "status"`.

No payload fields.

### wait

Answers with `Changes` once anything has changed since `since`, or after a while with none. This is how the shell hears about everything without polling. Start from `Status.seq`.

Discriminator: `"op": "wait"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `since` | `uint64` | **error** | emit normally |

### inbox

The conversations I am in that I would answer, starred first, then newest first; for `Unread` and `Mentions`, mentions first, then newest. In it: direct and group conversations, starred rows, rows the adapter lists, and channels that mention me (for 24 h after the mention, read or not). Never: hidden rows, message requests, rows with no message at all, archived rows that do not mention me, and anything quiet for 30 days that is not starred, unread, drafted or holding a failed send. Bot rows are in it with `bot` set: the shell folds them into one Apps row. Day groups are the shell's, from `updated`.

Discriminator: `"op": "inbox"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `network` | `nullable<Network>` | null | emit normally |
| `filter` | `InboxFilter` | type default | emit normally |
| `offset` | `uint32` | **error** | emit normally |
| `limit` | `uint32` | **error** | emit normally |

### spaces

Every Space of a network, or of all of them, in the network's order. Small by nature.

Discriminator: `"op": "spaces"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `network` | `nullable<Network>` | null | emit normally |

### tree

The groups of one Space and a page of its conversations in tree order. Asking is what makes chatd bring a Space up to date; a Space nobody opened costs nothing.

Discriminator: `"op": "tree"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `space` | `Key` | **error** | emit normally |
| `offset` | `uint32` | **error** | emit normally |
| `limit` | `uint32` | **error** | emit normally |
| `peek` | `boolean` | type default | omit when `std::ops::Not::not` is true |
| | | | Read what is stored and bring nothing up to date. The quick switcher reads many Spaces at once, and that must not subscribe to every one of them on the network. |

### conversation

One row, for after a `Conversation` change.

Discriminator: `"op": "conversation"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |

### collapse

Discriminator: `"op": "collapse"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `space` | `Key` | **error** | emit normally |
| `group` | `string` | **error** | emit normally |
| `collapsed` | `boolean` | **error** | emit normally |

### star

Discriminator: `"op": "star"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `starred` | `boolean` | **error** | emit normally |

### find

Conversations whose title contains `query`, across every Space, most recent first. From the cache alone: a channel of a Space never opened is not in it.

Discriminator: `"op": "find"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `network` | `nullable<Network>` | null | emit normally |
| `query` | `string` | **error** | emit normally |
| `limit` | `uint32` | **error** | emit normally |

### search_messages

Cached messages whose text contains `query`, newest first. `conversation` narrows to one conversation, `network` to one network. Hidden conversations and message requests stay out of it, as they stay out of everything that counts. From the cache alone: what a network itself finds lands as it answers, and is a later step.

Discriminator: `"op": "search_messages"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `nullable<Key>` | type default | omit when `Option::is_none` is true |
| `network` | `nullable<Network>` | type default | omit when `Option::is_none` is true |
| `query` | `string` | **error** | emit normally |
| `limit` | `uint32` | **error** | emit normally |

### set_draft

Keeps what the user typed and did not send. Empty text forgets it. Local: no network hears of it and no change is announced.

Discriminator: `"op": "set_draft"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `text` | `string` | **error** | emit normally |

### home

A network's own list of the conversations that belong to no Space (Discord's DMs, every Telegram chat, Teams' chats), as its home shows them: the network's pins in their order, then newest first. Hidden rows never; the archive and message requests only on their own `shelf`. With `folder`, the chats in that folder whatever their archive, the folder's own pins first. `counts` in the answer are this list's. Asking with `offset` 0 is what makes chatd bring it up to date.

Discriminator: `"op": "home"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `network` | `Network` | **error** | emit normally |
| `account` | `nullable<AccountKey>` | type default | omit when `Option::is_none` is true |
| `folder` | `nullable<string>` | type default | omit when `Option::is_none` is true |
| `shelf` | `Shelf` | type default | omit when `Shelf::is_main` is true |
| `offset` | `uint32` | **error** | emit normally |
| `limit` | `uint32` | **error** | emit normally |

### folders

The folders of a network's accounts in their order: Telegram's chat folders with their unread counts, Discord's server folders with their Spaces.

Discriminator: `"op": "folders"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `network` | `Network` | **error** | emit normally |

### threads

The threads the user follows in a Space (a Slack workspace's Threads view, a Discord server's joined threads), newest first. Asking with `offset` 0 is what makes chatd fetch the network's own list, once; it is kept fresh by the socket after that.

Discriminator: `"op": "threads"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `space` | `Key` | **error** | emit normally |
| `offset` | `uint32` | **error** | emit normally |
| `limit` | `uint32` | **error** | emit normally |

### topics

The topics of a forum (a Telegram forum group, a Discord forum), the network's pins first, then newest first. From the cache; opening a topic is opening a conversation.

Discriminator: `"op": "topics"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `forum` | `Key` | **error** | emit normally |
| `offset` | `uint32` | **error** | emit normally |
| `limit` | `uint32` | **error** | emit normally |

### in_voice

Voice channels and calls with a friend in them now, across Spaces: the Discord home's "In voice". From what chatd holds live; at most 50.

Discriminator: `"op": "in_voice"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `network` | `nullable<Network>` | null | emit normally |

### around

Who could I talk to now: pending requests counted, then people in a call, online, and talked to in the last 14 days, each A to Z, at most `AROUND_LIMIT`. Bots never.

Discriminator: `"op": "around"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `network` | `nullable<Network>` | null | emit normally |

### people

The lists the user owns (friends, contacts, direct partners), A to Z. With `query`, cached matches at once and the network's own search behind them as a `People` change. chatd decides when a network hears of it: a query of `SEARCH_MIN_CHARS` or more, the newest one only, once the typing has paused, to the connected accounts of `network`.

Discriminator: `"op": "people"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `network` | `nullable<Network>` | null | emit normally |
| `relation` | `nullable<Relation>` | null | emit normally |
| `query` | `nullable<string>` | null | emit normally |
| `offset` | `uint32` | **error** | emit normally |
| `limit` | `uint32` | **error** | emit normally |

### members

The visible rows of a conversation's member list. Never the whole list.

Discriminator: `"op": "members"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `offset` | `uint32` | **error** | emit normally |
| `limit` | `uint32` | **error** | emit normally |

### start_direct

The direct conversation with a person, created if there is none. Nothing reaches the other person until a message is sent.

Discriminator: `"op": "start_direct"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `person` | `Key` | **error** | emit normally |

### profile

One person's card, asked of the network when the card opens and kept five minutes. `space` is where it was opened from, for the nickname, roles and join date there.

Discriminator: `"op": "profile"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `person` | `Key` | **error** | emit normally |
| `space` | `nullable<Key>` | type default | omit when `Option::is_none` is true |

### conversation_info

What the info pane says of a conversation beyond its row. Asked of the network when the pane opens and kept five minutes.

Discriminator: `"op": "conversation_info"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |

### space_info

A Space's own info, opened from its name.

Discriminator: `"op": "space_info"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `space` | `Key` | **error** | emit normally |

### set_mute

The network's notification setting for a conversation. The row changes when the network says so.

Discriminator: `"op": "set_mute"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `notify` | `Notify` | **error** | emit normally |

### leave

Leaves a group conversation on the network. The shell asks once to confirm first.

Discriminator: `"op": "leave"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |

### close_direct

Closes a direct conversation, as the network's own ×: it leaves the list until a new message brings it back. Nothing is deleted.

Discriminator: `"op": "close_direct"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |

### pinned

The messages pinned in a conversation, asked of the network, newest first, at most `PINNED_LIMIT`.

Discriminator: `"op": "pinned"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |

### shared

The pictures, files or links said in a conversation, newest first, from what is cached: what the info pane lists under a person or a channel. `before` continues below a message already listed. With `search`, the network is asked instead, because the user clicked "Search all"; never otherwise.

Discriminator: `"op": "shared"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `kind` | `SharedKind` | **error** | emit normally |
| `before` | `nullable<string>` | type default | omit when `Option::is_none` is true |
| `limit` | `uint32` | **error** | emit normally |
| `search` | `boolean` | type default | omit when `is_false` is true |

### relate

Answer, withdraw or end a friendship, or block. The list changes when the network says so (a `People` change).

Discriminator: `"op": "relate"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `person` | `Key` | **error** | emit normally |
| `action` | `RelateAction` | **error** | emit normally |

### set_presence

Our own presence on one account, and the status text beside it: `None` leaves the text as it is, empty clears it.

Discriminator: `"op": "set_presence"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `account` | `AccountKey` | **error** | emit normally |
| `presence` | `Presence` | **error** | emit normally |
| `status` | `nullable<string>` | type default | omit when `Option::is_none` is true |

### watch

Discriminator: `"op": "watch"`.

Payload is `Watching`; merge its object/discriminator fields into this object, without a wrapper field.

### messages

A page of one conversation, oldest first. Reading is not marking read.

Discriminator: `"op": "messages"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `page` | `Page` | type default | emit normally |
| `limit` | `uint32` | **error** | emit normally |

### mark_read

The user saw the conversation up to this message: the window is active, the conversation is open and the message is on screen. Read here and on the network.

Discriminator: `"op": "mark_read"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `message_id` | `string` | **error** | emit normally |

### send

Answers at once with the message as `Pending`. `client_id` is made by the shell and comes back on the message; when the network accepts it the same row turns `Sent` under its real id, or `Failed` with the reason. Refused outright when the account is not connected.  `with` carries files (streamed by chatd from their paths, with `Change::Upload` as they go) and options; the pending message lists the files at once. Refused when it asks for more than the account's `Capabilities` allow.

Discriminator: `"op": "send"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `client_id` | `string` | **error** | emit normally |
| `text` | `string` | **error** | emit normally |
| `reply_to` | `nullable<string>` | type default | omit when `Option::is_none` is true |
| `with` | `Outgoing` | type default | omit when `Outgoing::is_plain` is true |

### cancel_send

Stops a send whose files are still uploading. It ends `Failed` ("Cancelled"), so Retry and Discard work on it as on any other.

Discriminator: `"op": "cancel_send"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `client_id` | `string` | **error** | emit normally |

### retry

Sends a `Failed` message again.

Discriminator: `"op": "retry"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `client_id` | `string` | **error** | emit normally |

### discard

Removes a `Failed` or `Pending` message that never left.

Discriminator: `"op": "discard"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `client_id` | `string` | **error** | emit normally |

### typing

The user's draft is changing. chatd decides how often the network hears of it.

Discriminator: `"op": "typing"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |

### react

Adds (`on`) or takes back our reaction. `emoji` is the emoji itself, or a custom one's `:name:` as `Reaction::emoji` spells it. Shown at once; what the network then says is what stays.

Discriminator: `"op": "react"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `message_id` | `string` | **error** | emit normally |
| `emoji` | `string` | **error** | emit normally |
| `on` | `boolean` | **error** | emit normally |

### reactions

What reactions the conversation takes from this account: asked when it opens, kept five minutes. chatd refuses a `React` these rules refuse, before the network hears of it.

Discriminator: `"op": "reactions"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |

### edit

Replaces the text of one of our own messages. Nothing changes on screen until the network accepts it; a refusal is the answer.

Discriminator: `"op": "edit"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `message_id` | `string` | **error** | emit normally |
| `text` | `string` | **error** | emit normally |

### delete

Deletes a message for everyone. Waits for the network, like `Edit`.

Discriminator: `"op": "delete"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `message_id` | `string` | **error** | emit normally |

### catalog

Custom emoji, stickers or GIFs for the picker, asked when its tab opens and never before, kept five minutes. `space` narrows custom emoji to one Space's; `query` searches; `cursor` continues a page. At most `CATALOG_LIMIT` items.

Discriminator: `"op": "catalog"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `account` | `AccountKey` | **error** | emit normally |
| `kind` | `CatalogKind` | **error** | emit normally |
| `space` | `nullable<Key>` | type default | omit when `Option::is_none` is true |
| `query` | `string` | type default | omit when `String::is_empty` is true |
| `cursor` | `nullable<string>` | type default | omit when `Option::is_none` is true |

### fetch

Asks for these files to be on disk. Answers with what is known now; each file that lands later is a `Media` change. Ask only for what is on screen.

Discriminator: `"op": "fetch"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `account` | `AccountKey` | **error** | emit normally |
| `ids` | `list<string>` | **error** | emit normally |
| `size` | `nullable<uint32>` | type default | omit when `Option::is_none` is true |
| | | | The longest side of the whole picture at the scale it is drawn, in device pixels (points times the screen's scale; for a cropped tile, the uncropped picture). Where the adapter registered size variants, chatd fetches the smallest one at least this large, and fetches again when the file on disk is smaller. Such a file answers with no `path` until the larger one lands. |
| `retry` | `boolean` | type default | omit when `is_false` is true |
| | | | The user asked again for files that failed. Without this a failed file is answered with its `failed` reason and nothing is fetched. |

### sign_in

Opens the network's sign-in and keeps the session. Answers when the user is done.

Discriminator: `"op": "sign_in"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `network` | `Network` | **error** | emit normally |
| `at` | `nullable<tuple(int32,int32)>` | type default | omit when `Option::is_none` is true |
| | | | The main window's top left corner in screen points, so the sign-in window opens over it and not on another display. |

### read_sessions

Reads again the sessions the keychain refused (`Keychain::denied`): the user's "Try again". Answers `Status` at once; the read goes on behind it.

Discriminator: `"op": "read_sessions"`.

No payload fields.

### sign_out

Forgets the account's session and everything stored for it. Waits up to 5 s for the network to end the session first.

Discriminator: `"op": "sign_out"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `account` | `AccountKey` | **error** | emit normally |

### sign_in_begin

Begins, or reads again, a sign-in the shell draws itself (`signin.rs`). Answers with the step to draw. For a network that signs in through a web page this is `Unsupported`.

Discriminator: `"op": "sign_in_begin"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `network` | `Network` | **error** | emit normally |

### sign_in_answer

What the user did about the step on show. Answers with the step to draw next.

Discriminator: `"op": "sign_in_answer"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `network` | `Network` | **error** | emit normally |
| `input` | `SignInInput` | **error** | emit normally |

### sign_in_cancel

The user closed the sheet. Nothing is kept.

Discriminator: `"op": "sign_in_cancel"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `network` | `Network` | **error** | emit normally |

### call_start

Joins or rings. Starts mediad. One call at a time. Refused with `Unsupported`, and no mediad, unless the conversation's `call` is `Native`.

Discriminator: `"op": "call_start"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |

### call_accept

Answers the incoming ring. Starts mediad.

Discriminator: `"op": "call_accept"`.

No payload fields.

### call_decline

Stops the incoming ring for both sides. mediad never starts.

Discriminator: `"op": "call_decline"`.

No payload fields.

### call_end

Leaves. Stops mediad.

Discriminator: `"op": "call_end"`.

No payload fields.

### call_set

Discriminator: `"op": "call_set"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `muted` | `boolean` | **error** | emit normally |
| `deafened` | `boolean` | **error** | emit normally |

### handoff

Where the official app takes this conversation's call.

Discriminator: `"op": "handoff"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |

### media

Discriminator: `"op": "media"`.

Payload is `MediaRequest`; merge its object/discriminator fields into this object, without a wrapper field.

### play

A voice message or audio file: play, pause, seek, speed, stop. Answers `Ok`; the rest is `Change::Playback`.

Discriminator: `"op": "play"`.

Payload is `PlayRequest`; merge its object/discriminator fields into this object, without a wrapper field.

### settings

Every stored setting (`settings`). Missing ones are at their defaults.

Discriminator: `"op": "settings"`.

No payload fields.

### set

Stores one setting, or with `None` returns it to its default. Answered `Ok`, then `Change::Settings`. Refused unless `settings::valid` (or, for `None`, `settings::known`).

Discriminator: `"op": "set"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `scope` | `string` | **error** | emit normally |
| `key` | `string` | **error** | emit normally |
| `value` | `nullable<string>` | type default | emit normally |

### reset_settings

Reset all settings: every stored row goes, so every setting is at its default.

Discriminator: `"op": "reset_settings"`.

No payload fields.

### shutdown

Stops chatd: ⌘Q, and closing the window while Keep receiving is off. Answered `Ok` first; a call is left on the network before the process exits.

Discriminator: `"op": "shutdown"`.

No payload fields.

### storage

What tinyclient keeps on this Mac, in bytes (Settings › Storage).

Discriminator: `"op": "storage"`.

No payload fields.

### clear

Deletes every cached message and file. Sessions, drafts and settings stay.

Discriminator: `"op": "clear"`.

No payload fields.

### prunable

How much a retention of `days` would delete now.

Discriminator: `"op": "prunable"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `days` | `uint32` | **error** | emit normally |

### test_microphone

The microphone test: on, the level arrives as `Change::Meter` ten times a second until off, 30 s, or a call starts. In a call it is the call's own meter.

Discriminator: `"op": "test_microphone"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `on` | `boolean` | **error** | emit normally |

### test_sound

Plays the test sound on the call speaker (V2): in the call's mediad, or one started for it.

Discriminator: `"op": "test_sound"`.

No payload fields.

## Response

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

Internally tagged object: discriminator `op`.

### pong

Discriminator: `"op": "pong"`.

No payload fields.

### ok

Done, with nothing to say.

Discriminator: `"op": "ok"`.

No payload fields.

### status

Discriminator: `"op": "status"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `networks` | `list<NetworkStatus>` | **error** | emit normally |
| `accounts` | `list<AccountStatus>` | **error** | emit normally |
| `media` | `Media` | **error** | emit normally |
| `call` | `nullable<Call>` | null | emit normally |
| `seq` | `uint64` | **error** | emit normally |
| | | | Where `Wait` starts from. |
| `keychain` | `Keychain` | type default | omit when `Keychain::is_settled` is true |
| | | | What chatd is doing with the keychain: reading, waiting on macOS, refused. |
| `started` | `uint64` | type default | emit normally |
| | | | When this chatd started, unix milliseconds. A new value means it restarted: read everything on screen again. |

### changes

Discriminator: `"op": "changes"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `seq` | `uint64` | **error** | emit normally |
| | | | Pass this to the next `Wait`. |
| `reset` | `boolean` | **error** | emit normally |
| | | | chatd no longer knows what changed since `since` (it restarted, or the shell fell too far behind): read everything on screen again. |
| `changes` | `list<Change>` | **error** | emit normally |

### conversations

Discriminator: `"op": "conversations"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversations` | `list<Conversation>` | **error** | emit normally |
| `total` | `uint32` | **error** | emit normally |
| | | | How many rows the request matches in all. |
| `counts` | `InboxCounts` | type default | emit normally |
| | | | For `Inbox`: what each filter would hold. Zero for `Find`. |

### conversation

Discriminator: `"op": "conversation"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Conversation` | **error** | emit normally |

### spaces

Discriminator: `"op": "spaces"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `spaces` | `list<Space>` | **error** | emit normally |

### tree

Discriminator: `"op": "tree"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `space` | `Key` | **error** | emit normally |
| `groups` | `list<Group>` | **error** | emit normally |
| `conversations` | `list<Conversation>` | **error** | emit normally |
| `total` | `uint32` | **error** | emit normally |

### people

Discriminator: `"op": "people"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `people` | `list<Person>` | **error** | emit normally |
| `total` | `uint32` | **error** | emit normally |

### members

Discriminator: `"op": "members"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `pending` | `boolean` | type default | omit when `is_false` is true |
| | | | Discord cache miss: rows will arrive through the active viewport subscription. |
| `conversation` | `Key` | **error** | emit normally |
| `sections` | `list<MemberSection>` | **error** | emit normally |
| `offset` | `uint32` | **error** | emit normally |
| `members` | `list<Person>` | **error** | emit normally |

### watching

What is known now about what the shell watches.

Discriminator: `"op": "watching"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `people` | `list<Person>` | **error** | emit normally |
| `typists` | `list<Typist>` | **error** | emit normally |

### messages

Discriminator: `"op": "messages"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `messages` | `list<Message>` | **error** | emit normally |
| `last_read` | `nullable<string>` | null | emit normally |
| | | | Where the user had read to when asked. |
| `older` | `boolean` | **error** | emit normally |
| | | | The cache holds messages older than the first one here. |
| `newer` | `boolean` | **error** | emit normally |
| | | | The cache holds messages newer than the last one here. |

### message_hits

Answers `SearchMessages`: the newest hits first, at most the limit asked for.

Discriminator: `"op": "message_hits"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `hits` | `list<MessageHit>` | **error** | emit normally |

### sent

Discriminator: `"op": "sent"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `message` | `Message` | **error** | emit normally |

### media

Discriminator: `"op": "media"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `files` | `list<MediaFile>` | **error** | emit normally |

### link

Discriminator: `"op": "link"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `url` | `string` | **error** | emit normally |

### profile

Discriminator: `"op": "profile"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `profile` | `Profile` | **error** | emit normally |

### shared

Discriminator: `"op": "shared"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `items` | `list<SharedItem>` | **error** | emit normally |
| `more` | `boolean` | **error** | emit normally |
| | | | The cache holds older messages that were not looked at yet, or the network has more. |
| `complete` | `boolean` | type default | omit when `is_false` is true |
| | | | The list is the network's own and whole (a search was asked, or the network keeps the list). False: it is only what is in the messages loaded here, and must say so. |
| `total` | `nullable<uint32>` | type default | omit when `Option::is_none` is true |
| | | | The exact total, only where the network counted. |

### folders

Discriminator: `"op": "folders"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `folders` | `list<Folder>` | **error** | emit normally |

### around

Discriminator: `"op": "around"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `requests` | `uint32` | **error** | emit normally |
| | | | Incoming requests waiting on me (Discord's Pending), counted only. |
| `in_call` | `list<Person>` | **error** | emit normally |
| `online` | `list<Person>` | **error** | emit normally |
| `recent` | `list<Person>` | **error** | emit normally |

### conversation_info

Boxed, as `Profile` is: few answers are one, and every answer would carry its size.

Discriminator: `"op": "conversation_info"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `info` | `ConversationInfo` | **error** | emit normally |

### space_info

Discriminator: `"op": "space_info"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `info` | `SpaceInfo` | **error** | emit normally |

### pinned

Discriminator: `"op": "pinned"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `messages` | `list<Message>` | **error** | emit normally |

### reactions

Discriminator: `"op": "reactions"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `rules` | `ReactionRules` | **error** | emit normally |

### catalog

Discriminator: `"op": "catalog"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `items` | `list<CatalogItem>` | **error** | emit normally |
| `cursor` | `nullable<string>` | type default | omit when `Option::is_none` is true |
| | | | Pass back for the next page; `None` at the end. |

### sign_in

Where a sign-in the shell draws stands.

Discriminator: `"op": "sign_in"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `network` | `Network` | **error** | emit normally |
| `step` | `SignInStep` | **error** | emit normally |

### error

Discriminator: `"op": "error"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `code` | `ErrorCode` | **error** | emit normally |
| `detail` | `string` | **error** | emit normally |

### settings

Discriminator: `"op": "settings"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `values` | `list<settings::Setting>` | **error** | emit normally |

### storage

Bytes on this Mac: the message database and the cached images and files.

Discriminator: `"op": "storage"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `messages` | `uint64` | **error** | emit normally |
| `files` | `uint64` | **error** | emit normally |

### prunable

What a shorter retention would delete: messages, and about how many bytes of them.

Discriminator: `"op": "prunable"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `messages` | `uint64` | **error** | emit normally |
| `bytes` | `uint64` | **error** | emit normally |

## Change

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

One thing that changed. The shell asks again for exactly that; the ephemeral kinds carry their whole new value and never cause a list to be read again.

Internally tagged object: discriminator `what`.

### status

Links, accounts or their totals: ask `Status`.

Discriminator: `"what": "status"`.

No payload fields.

### conversation

A row's title, preview, order or unread state: ask `Conversation`, or the list it is in.

Discriminator: `"what": "conversation"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |

### messages

Messages arrived, were edited, deleted, reacted to or changed send state: ask `Messages`.

Discriminator: `"what": "messages"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |

### spaces

Spaces were added, removed or reordered: ask `Spaces`.

Discriminator: `"what": "spaces"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `account` | `AccountKey` | **error** | emit normally |

### tree

A Space's groups or conversations: ask `Tree`.

Discriminator: `"what": "tree"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `space` | `Key` | **error** | emit normally |

### people

The owned lists or a search result: ask `People`.

Discriminator: `"what": "people"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `account` | `AccountKey` | **error** | emit normally |

### members

Rows of a conversation's member list were added, removed or moved: ask `Members` again for the rows on screen.

Discriminator: `"what": "members"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |

### media

A requested file is on disk (`path`), or could not be fetched (`failed` says why).

Discriminator: `"what": "media"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `account` | `AccountKey` | **error** | emit normally |
| `file` | `MediaFile` | **error** | emit normally |

### occupants

Ephemeral. Who is in a voice channel now; no people and a total of 0 when it emptied.

Discriminator: `"what": "occupants"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `occupants` | `Occupants` | **error** | emit normally |

### searched

Ephemeral. A network finished the search for `query`, whether or not it found anyone.

Discriminator: `"what": "searched"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `account` | `AccountKey` | **error** | emit normally |
| `query` | `string` | **error** | emit normally |

### typing

Ephemeral. Everyone typing in the conversation now; empty when they stopped.

Discriminator: `"what": "typing"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `typists` | `list<Typist>` | **error** | emit normally |

### folders

A network's folders, or their counts: ask `Folders`.

Discriminator: `"what": "folders"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `account` | `AccountKey` | **error** | emit normally |

### presence

Ephemeral. Presence, status and what they are doing, all of it.

Discriminator: `"what": "presence"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `person` | `Key` | **error** | emit normally |
| `presence` | `Presence` | **error** | emit normally |
| `status` | `string` | **error** | emit normally |
| `emoji` | `string` | type default | omit when `String::is_empty` is true |
| `activity` | `nullable<Activity>` | type default | omit when `Option::is_none` is true |

### upload

Ephemeral. How far the files of a pending message have gone, in bytes, at most four times a second. Its outcome is the message's own change.

Discriminator: `"what": "upload"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `client_id` | `string` | **error** | emit normally |
| `sent` | `uint64` | **error** | emit normally |
| `total` | `uint64` | **error** | emit normally |

### call

Ephemeral. The call as it is now: who is speaking, mute, state. `None` when it is over.

Discriminator: `"what": "call"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `call` | `nullable<Call>` | null | emit normally |

### sign_in

Ephemeral. A sign-in the shell is drawing moved on by itself: the code was scanned, or ran out and was replaced.

Discriminator: `"what": "sign_in"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `network` | `Network` | **error** | emit normally |
| `step` | `SignInStep` | **error** | emit normally |

### playback

Ephemeral. The voice message or audio file playing, paused or just ended; `None` once stopped.

Discriminator: `"what": "playback"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `playback` | `nullable<Playback>` | null | emit normally |

### settings

A setting was stored or reset: ask `Settings`.

Discriminator: `"what": "settings"`.

No payload fields.

### meter

Ephemeral. The microphone test's level, 0 to 100; `None` once the test is over.

Discriminator: `"what": "meter"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `level` | `nullable<uint8>` | null | emit normally |

## AccountKey

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

One signed-in identity. `account` is chosen by the adapter and is stable across restarts: a Slack team id, a Discord user id.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `network` | `Network` | **error** | emit normally |
| `account` | `string` | **error** | emit normally |

## AccountStatus

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `key` | `AccountKey` | **error** | emit normally |
| `name` | `string` | **error** | emit normally |
| | | | The workspace's name, or the user's own name where an account is a person. |
| `link` | `Link` | **error** | emit normally |
| `detail` | `string` | type default | omit when `String::is_empty` is true |
| | | | Why the link is what it is, in words, when the network said. |
| `me` | `string` | type default | omit when `String::is_empty` is true |
| | | | Our own person id on this account. |
| `attention` | `uint32` | **error** | emit normally |
| | | | The sum of the numbers on this account's rows (see `Conversation::badge`). |
| `unread` | `boolean` | **error** | emit normally |
| | | | Something unmuted is unread that has no number. |
| `reconnecting` | `boolean` | type default | omit when `is_false` is true |
| | | | With `Offline`: the connection dropped and chatd is trying again within seconds. False while `Offline` means it has not connected yet, or has backed off to trying rarely. |
| `required` | `string` | type default | omit when `String::is_empty` is true |
| | | | Something only the network's own app can do stands in the way (a captcha, a verification), in words: "Discord wants you to verify your account in its app." Empty when nothing does. The link may be anything; `Connected` with this set still fails most requests. |
| `avatar` | `nullable<MediaFile>` | type default | omit when `Option::is_none` is true |
| | | | Our own picture on this account. |
| `presence` | `Presence` | type default | emit normally |
| | | | Our own presence and status text as the network shows them to others. |
| `status` | `string` | type default | omit when `String::is_empty` is true |
| `can` | `Capabilities` | type default | omit when `Capabilities::is_none` is true |
| | | | What this account may send: file limits, pickers and options. All off until the adapter reports them. |

## Activity

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `kind` | `ActivityKind` | **error** | emit normally |
| `name` | `string` | type default | omit when `String::is_empty` is true |
| | | | The game, the song's service, the channel: "Hades", "Spotify", "#trail". At most 128 characters. |
| `place` | `string` | type default | omit when `String::is_empty` is true |
| | | | Where, when it is somewhere: the Space of a voice channel. |
| `conversation` | `nullable<Key>` | type default | omit when `Option::is_none` is true |
| | | | The conversation to open for it (the voice channel), where there is one. |

## ActivityKind

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

What someone is doing now. Live, like presence: never stored.

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### playing

JSON value: `"playing"`.

No payload fields.

### listening

JSON value: `"listening"`.

No payload fields.

### watching

JSON value: `"watching"`.

No payload fields.

### streaming

JSON value: `"streaming"`.

No payload fields.

### competing

JSON value: `"competing"`.

No payload fields.

### in_voice

In a voice channel. `name` is the channel, `place` its Space.

JSON value: `"in_voice"`.

No payload fields.

### in_call

In a direct call.

JSON value: `"in_call"`.

No payload fields.

### in_meeting

JSON value: `"in_meeting"`.

No payload fields.

### presenting

JSON value: `"presenting"`.

No payload fields.

### huddle

In a Slack huddle.

JSON value: `"huddle"`.

No payload fields.

## Attachment

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/message.rs).

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `name` | `string` | **error** | emit normally |
| `file` | `MediaFile` | **error** | emit normally |
| | | | The file itself: its `bytes` is the size shown on a file row. |
| `thumb` | `nullable<MediaFile>` | type default | omit when `Option::is_none` is true |
| | | | What an image, video or GIF shows inline. Small enough to fetch when on screen. |
| `mime` | `string` | type default | omit when `String::is_empty` is true |
| `duration` | `uint32` | type default | omit when `is_zero` is true |
| | | | Seconds, for audio and video. |
| `spoiler` | `boolean` | type default | omit when `is_false` is true |
| | | | Hidden until the user asks to see it. |
| `sticker` | `boolean` | type default | omit when `is_false` is true |
| | | | A sticker: drawn at its own size with no frame, and its transparency kept. |
| `waveform` | `list<uint8>` | type default | omit when `Vec::is_empty` is true |
| | | | A voice message's loudness over time, one byte a bar, at most `WAVEFORM_LIMIT`. Its length in seconds is `duration`. |
| `round` | `boolean` | type default | omit when `is_false` is true |
| | | | A round video message (Telegram's): drawn in a circle. |

## Call

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/call.rs).

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `state` | `CallState` | **error** | merge referenced object fields into parent; no field named state |
| `participants` | `list<Participant>` | **error** | emit normally |
| | | | Everyone in the call but us. |
| `muted` | `boolean` | **error** | emit normally |
| `deafened` | `boolean` | **error** | emit normally |
| `joined` | `int64` | **error** | emit normally |
| | | | Unix seconds the call was joined. 0 before that. |
| `input` | `string` | type default | omit when `String::is_empty` is true |
| | | | The microphone and speaker in use, as the system names them. Empty until mediad says. |
| `output` | `string` | type default | omit when `String::is_empty` is true |
| `engine_linked` | `boolean` | **error** | emit normally |
| | | | False until mediad links a real media engine. The lifecycle runs either way. |
| `video` | `list<VideoStream>` | **error** | emit normally |
| `speaking` | `boolean` | type default | omit when `is_false` is true |
| | | | We are heard right now: our microphone is open and carrying speech. |
| `level` | `nullable<uint8>` | type default | omit when `Option::is_none` is true |
| | | | Our microphone's level, 0 to 100. Only while the shell asked for it with `MediaRequest::Meter` (the device menu is open); `None` the rest of the time, so a call nobody is adjusting sends no changes for it. |
| `inputs` | `list<string>` | type default | omit when `Vec::is_empty` is true |
| | | | Every microphone and speaker the system lists, at most `DEVICES_LIMIT` of each. Empty until mediad says. |
| `outputs` | `list<string>` | type default | omit when `Vec::is_empty` is true |

## CallFailure

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/call.rs).

Why a call is not happening, for the one line the dock shows.

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### no_answer

Nobody answered, or they declined.

JSON value: `"no_answer"`.

No payload fields.

### refused

The network refused the voice connection.

JSON value: `"refused"`.

No payload fields.

### encryption

The network requires a newer encryption than this build speaks (Discord close code 4017).

JSON value: `"encryption"`.

No payload fields.

### lost

No reply in time, or the packets stopped and did not come back.

JSON value: `"lost"`.

No payload fields.

### audio

The microphone or speaker could not be opened, or permission was denied.

JSON value: `"audio"`.

No payload fields.

### engine

mediad could not start, or died.

JSON value: `"engine"`.

No payload fields.

## CallState

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/call.rs).

Internally tagged object: discriminator `state`.

### ringing_out

We are calling and nobody has answered. It stays this, whatever our own media is doing, until the adapter says the other side picked up.

Discriminator: `"state": "ringing_out"`.

No payload fields.

### ringing_in

Someone is calling us. mediad is not running.

Discriminator: `"state": "ringing_in"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `from` | `string` | **error** | emit normally |

### connecting

mediad is up and joining. Not yet a call: nobody can hear anybody.

Discriminator: `"state": "connecting"`.

No payload fields.

### joined

The network confirmed the join and media flows. The only state drawn as "in a call".

Discriminator: `"state": "joined"`.

No payload fields.

### reconnecting

Media stopped; mediad is trying to get it back.

Discriminator: `"state": "reconnecting"`.

No payload fields.

### failed

Discriminator: `"state": "failed"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `reason` | `CallFailure` | **error** | emit normally |
| `detail` | `string` | **error** | emit normally |

## CallSupport

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

What pressing the call button of a conversation does.

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### none

Default variant for this type.

JSON value: `"none"`.

No payload fields.

### native

tinyclient carries the call itself.

JSON value: `"native"`.

No payload fields.

### handoff

The official app does: ask `Handoff` for the link and open it.

JSON value: `"handoff"`.

No payload fields.

## Capabilities

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

What an account may send, as the session says (the plan, the workspace's settings). A control the account lacks is absent in the shell, never disabled. Nothing is allowed until the adapter reports it (`Context::capabilities`).

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `max_file_bytes` | `uint64` | type default | omit when `crate::is_zero64` is true |
| | | | Largest file, in bytes. 0: files cannot be sent. |
| `max_files` | `uint32` | type default | omit when `is_zero` is true |
| | | | Most files in one message. |
| `caption_limit` | `uint32` | type default | omit when `is_zero` is true |
| | | | Longest caption under files, in characters. 0: the text limit. |
| `spoiler` | `boolean` | type default | omit when `is_false` is true |
| | | | Per-file options. |
| `as_file` | `boolean` | type default | omit when `is_false` is true |
| `gifs` | `boolean` | type default | omit when `is_false` is true |
| | | | The network has a GIF search tinyclient can ask (`Catalog` with `Gifs`). |
| `stickers` | `boolean` | type default | omit when `is_false` is true |
| `custom_emoji` | `EmojiScope` | type default | emit normally |
| `silent` | `boolean` | type default | omit when `is_false` is true |
| | | | `Outgoing::silent`, `Outgoing::schedule`, `Outgoing::suppress_embeds` and `Outgoing::ping` are carried out by the network. |
| `schedule` | `boolean` | type default | omit when `is_false` is true |
| `suppress_embeds` | `boolean` | type default | omit when `is_false` is true |
| `reply_ping` | `boolean` | type default | omit when `is_false` is true |
| `edit_window` | `uint32` | type default | omit when `is_zero` is true |
| | | | Seconds after sending that an edit is still allowed. 0: no limit. |

## Card

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/message.rs).

What a bot or app posts instead of plain text: an embed, a block of fields. Drawn as one framed card under the message's text. Every string is cut to a fixed length on its way in.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `title` | `string` | type default | omit when `String::is_empty` is true |
| `text` | `string` | type default | omit when `String::is_empty` is true |
| `fields` | `list<tuple(string,string)>` | type default | omit when `Vec::is_empty` is true |
| | | | Label and value, in the network's order, at most `CARD_FIELDS`. |
| `footer` | `string` | type default | omit when `String::is_empty` is true |
| `color` | `nullable<uint32>` | type default | omit when `Option::is_none` is true |
| | | | The accent the network gave it, `0xRRGGBB`. |

## CatalogItem

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

One custom emoji, sticker or GIF in a picker.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `id` | `string` | **error** | emit normally |
| | | | What `Pick::id` or a reaction names. For a custom emoji, the id of its registered file. |
| `name` | `string` | type default | omit when `String::is_empty` is true |
| | | | `:name:` for an emoji, a sticker's emoji or a GIF's title. |
| `file` | `nullable<MediaFile>` | type default | omit when `Option::is_none` is true |
| | | | Its still preview, a registered file the shell asks `Fetch` for when it is on screen. |
| `pack` | `string` | type default | omit when `String::is_empty` is true |
| | | | The pack or Space it belongs to, for the picker's sections. |
| `animated` | `boolean` | type default | omit when `is_false` is true |

## CatalogKind

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### emoji

The account's custom emoji (Unicode emoji are the shell's own list).

JSON value: `"emoji"`.

No payload fields.

### stickers

JSON value: `"stickers"`.

No payload fields.

### gifs

JSON value: `"gifs"`.

No payload fields.

## CodeVia

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/signin.rs).

How a login code reached the user.

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### app

A message in the network's own app on another device.

JSON value: `"app"`.

No payload fields.

### sms

JSON value: `"sms"`.

No payload fields.

### call

JSON value: `"call"`.

No payload fields.

### email

JSON value: `"email"`.

No payload fields.

### other

JSON value: `"other"`.

No payload fields.

## Contact

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `kind` | `ContactKind` | **error** | emit normally |
| `value` | `string` | **error** | emit normally |
| `masked` | `boolean` | type default | omit when `is_false` is true |
| | | | Drawn masked ("+44 •••• ••42 · Show") until clicked, each time. Phone numbers always. |

## ContactKind

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

How a phone number or address on a profile is drawn.

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### email

JSON value: `"email"`.

No payload fields.

### phone

JSON value: `"phone"`.

No payload fields.

### other

JSON value: `"other"`.

No payload fields.

## Content

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/call.rs).

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### share

The one screen share being sent or watched.

JSON value: `"share"`.

No payload fields.

### speaker

The active speaker's camera.

JSON value: `"speaker"`.

No payload fields.

## Conversation

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

One row of the Inbox or of a Space's tree. No message bodies beyond the preview.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `key` | `Key` | **error** | emit normally |
| `kind` | `ConversationKind` | **error** | emit normally |
| `title` | `string` | **error** | emit normally |
| `space` | `nullable<string>` | type default | omit when `Option::is_none` is true |
| | | | The Space it is in. Direct conversations have none, except on a network that keeps them inside a Space (see `GroupKind::Directs`). |
| `space_title` | `string` | type default | omit when `String::is_empty` is true |
| | | | That Space's name, so a row can say where it is without a second request. |
| `group` | `nullable<string>` | type default | omit when `Option::is_none` is true |
| | | | The `Group` it sits under in its Space's tree. |
| `group_title` | `string` | type default | omit when `String::is_empty` is true |
| | | | That Group's name. |
| `topic` | `string` | type default | omit when `String::is_empty` is true |
| | | | What the conversation is for, as its owners wrote it. One line, cut to 300 characters. |
| `parent` | `nullable<string>` | type default | omit when `Option::is_none` is true |
| | | | For a `Thread`: the conversation it hangs off, and the message there that started it. |
| `root` | `nullable<string>` | type default | omit when `Option::is_none` is true |
| `position` | `int32` | type default | emit normally |
| | | | The network's own order inside its Space. |
| `avatar` | `nullable<MediaFile>` | type default | omit when `Option::is_none` is true |
| `peer` | `nullable<string>` | type default | omit when `Option::is_none` is true |
| | | | The other person of a `Direct` conversation, for presence. |
| `unread` | `uint32` | type default | omit when `is_zero` is true |
| | | | Unread messages. For a channel the network may only say "some", which is 1. |
| `mentions` | `uint32` | type default | omit when `is_zero` is true |
| | | | Unread messages that mention me. |
| `muted` | `boolean` | type default | omit when `is_false` is true |
| | | | Muted on the network. Drawn dimmed, never a dot, still a quiet mention count. |
| `starred` | `boolean` | type default | omit when `is_false` is true |
| | | | Pinned to the top of the Inbox. Local; the network never hears of it. |
| `preview` | `string` | type default | omit when `String::is_empty` is true |
| `updated` | `int64` | type default | emit normally |
| | | | Unix seconds of the newest message. |
| `last_read` | `nullable<string>` | type default | omit when `Option::is_none` is true |
| | | | The newest message read, for the "New" divider. `Messages` answers with the value from before the shell marks anything read. |
| `call` | `CallSupport` | type default | emit normally |
| `occupants` | `nullable<Occupants>` | type default | omit when `Option::is_none` is true |
| | | | Who is in it, for a voice channel someone is in. `None` when it is empty or unknown. |
| `read_only` | `boolean` | type default | omit when `is_false` is true |
| | | | I may read it but not post in it. |
| `private` | `boolean` | type default | omit when `is_false` is true |
| | | | Only invited people see it: drawn with a lock. |
| `draft` | `string` | type default | omit when `String::is_empty` is true |
| | | | What the user had typed and not sent, kept by chatd across restarts (`SetDraft`). |
| `folders` | `list<string>` | type default | omit when `Vec::is_empty` is true |
| | | | The folders it is in (Telegram's chat folders), by `Folder::key` id. A chat in two folders is in both. At most `FOLDERS_PER_ROW`. |
| `archived` | `boolean` | type default | omit when `is_false` is true |
| | | | In the network's archive: out of the Inbox and every count unless it mentions me. |
| `pin` | `nullable<int32>` | type default | omit when `Option::is_none` is true |
| | | | Pinned on the network, and where among the pins (lowest first). Separate from `starred`, which is tinyclient's own. |
| `hidden` | `boolean` | type default | omit when `is_false` is true |
| | | | Hidden on the network (a Teams chat the user hid): never listed. The adapter unhides it when a new message arrives, as the network does. |
| `followed` | `boolean` | type default | omit when `is_false` is true |
| | | | A followed thread (one the user joined or replied in): the Threads list holds these. |
| `bot` | `boolean` | type default | omit when `is_false` is true |
| | | | The other side is a bot or an app. Never among people: the Inbox folds these into one Apps row, and their plain unread raises no number anywhere. |
| `meeting` | `boolean` | type default | omit when `is_false` is true |
| | | | A meeting's chat (Teams). The shell moves one quiet for 14 days (`updated`) into a collapsed Meetings group. |
| `special` | `Special` | type default | omit when `Special::is_none` is true |
| `mark` | `nullable<Mark>` | type default | omit when `Option::is_none` is true |
| `opted_out` | `boolean` | type default | omit when `is_false` is true |
| | | | The user did not opt in to it (Discord's "show all channels" off): drawn only under the tree's "Browse n more channels". |
| `quiet` | `boolean` | type default | omit when `is_false` is true |
| | | | Filled by chatd on reading: nothing said in 30 days, nothing unread, not starred and no draft. Slack folds these into "n quiet channels". |
| `preview_from` | `string` | type default | omit when `String::is_empty` is true |
| | | | Who said the newest message, in a group or channel. Empty when it was me (`preview_mine`). |
| `preview_mine` | `boolean` | type default | omit when `is_false` is true |
| `seen` | `boolean` | type default | omit when `is_false` is true |
| | | | My newest message has been read by the other side (Telegram's ✓✓, Teams' "Seen"). |

## ConversationInfo

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

A conversation's info pane: what the row does not carry, asked of the network once when the pane opens and kept five minutes.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Conversation` | **error** | emit normally |
| `description` | `string` | type default | omit when `String::is_empty` is true |
| | | | The topic or about text in full, at most 4,000 characters. |
| `members` | `nullable<uint32>` | type default | omit when `Option::is_none` is true |
| | | | How many are in it, and how many of them are online, where the network counts. The `@everyone` / `@channel` confirm uses `members`. |
| `online` | `nullable<uint32>` | type default | omit when `Option::is_none` is true |
| `created` | `nullable<int64>` | type default | omit when `Option::is_none` is true |
| | | | Unix seconds, and who made it. |
| `creator` | `string` | type default | omit when `String::is_empty` is true |
| `notify` | `Notify` | type default | emit normally |
| `pinned` | `nullable<uint32>` | type default | omit when `Option::is_none` is true |
| | | | How many messages are pinned, where the network says. |
| `external` | `string` | type default | omit when `String::is_empty` is true |
| | | | The other organization of a shared channel (Slack Connect, a Teams shared channel). |
| `link` | `string` | type default | omit when `String::is_empty` is true |
| | | | The public link (`t.me/name`), where there is one. |

## ConversationKind

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### direct

JSON value: `"direct"`.

No payload fields.

### group

A group direct message.

JSON value: `"group"`.

No payload fields.

### channel

JSON value: `"channel"`.

No payload fields.

### announcement

JSON value: `"announcement"`.

No payload fields.

### voice

JSON value: `"voice"`.

No payload fields.

### forum

JSON value: `"forum"`.

No payload fields.

### thread

JSON value: `"thread"`.

No payload fields.

## Cue

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/call.rs).

The short sounds mediad makes inside a call (`docs/design/09-settings.md` §8).

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### joined

JSON value: `"joined"`.

No payload fields.

### left

JSON value: `"left"`.

No payload fields.

### muted

JSON value: `"muted"`.

No payload fields.

### unmuted

JSON value: `"unmuted"`.

No payload fields.

### deafened

JSON value: `"deafened"`.

No payload fields.

### undeafened

JSON value: `"undeafened"`.

No payload fields.

### lost

JSON value: `"lost"`.

No payload fields.

### back

JSON value: `"back"`.

No payload fields.

### test

"Play test sound": the join cue, whatever the switches say.

JSON value: `"test"`.

No payload fields.

## Dave

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/call.rs).

What Discord's end-to-end encryption needs from mediad.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `max_version` | `uint16` | **error** | emit normally |
| | | | The highest protocol version to offer in the voice identify. 0 offers none. |
| `required` | `boolean` | **error** | emit normally |
| | | | The call cannot proceed unencrypted: fail with `Encryption` rather than fall back. |

## Direction

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/call.rs).

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### encode

JSON value: `"encode"`.

No payload fields.

### decode

JSON value: `"decode"`.

No payload fields.

## EmojiScope

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

Which of a custom emoji set this account may send.

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### none

Default variant for this type.

None at all (Telegram without Premium).

JSON value: `"none"`.

No payload fields.

### space

Only the Space's own, where the message is said (Discord without Nitro).

JSON value: `"space"`.

No payload fields.

### all

Every custom emoji the account can see (Slack's workspace set, Discord with Nitro).

JSON value: `"all"`.

No payload fields.

## ErrorCode

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### offline

The account's socket is down, so nothing was sent or stored.

JSON value: `"offline"`.

No payload fields.

### not_found

JSON value: `"not_found"`.

No payload fields.

### call_active

JSON value: `"call_active"`.

No payload fields.

### no_call

JSON value: `"no_call"`.

No payload fields.

### media

JSON value: `"media"`.

No payload fields.

### sign_in

Sign-in was cancelled (the window was closed) or failed.

JSON value: `"sign_in"`.

No payload fields.

### sign_in_unreachable

The network's sign-in page could not be loaded.

JSON value: `"sign_in_unreachable"`.

No payload fields.

### sign_in_blocked

The user's organization does not allow this kind of sign-in.

JSON value: `"sign_in_blocked"`.

No payload fields.

### unsupported

This network has no adapter, or its adapter does not do this yet.

JSON value: `"unsupported"`.

No payload fields.

### refused

The network said no. `detail` is its reason, in words the user can read.

JSON value: `"refused"`.

No payload fields.

### too_large

The answer would not fit in one frame. Ask for a smaller page.

JSON value: `"too_large"`.

No payload fields.

### internal

JSON value: `"internal"`.

No payload fields.

## Folder

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

One folder of an account. On Telegram a folder is a filter over the chat list: a chat is in every folder that names it (`Conversation::folders`). On Discord a server folder groups Spaces (`spaces`). `unread` and `mentions` are filled by chatd.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `key` | `Key` | **error** | emit normally |
| | | | The account and the network's id of the folder. |
| `name` | `string` | type default | omit when `String::is_empty` is true |
| | | | May be empty: an unnamed Discord folder is shown as its first three servers' names. |
| `position` | `int32` | **error** | emit normally |
| | | | The network's order of folders. |
| `color` | `nullable<uint32>` | type default | omit when `Option::is_none` is true |
| | | | `0xRRGGBB`, where the network gives folders a colour (Discord). |
| `spaces` | `list<string>` | type default | omit when `Vec::is_empty` is true |
| | | | The Spaces it holds, in the user's order (Discord), at most `FOLDER_MEMBERS`. |
| `unread` | `uint32` | type default | omit when `is_zero` is true |
| | | | Conversations in it with unread messages that are not muted: what Telegram counts on a folder chip. For a folder of Spaces, the conversations of those Spaces. |
| `mentions` | `uint32` | type default | omit when `is_zero` is true |

## Forwarded

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/message.rs).

Where a forwarded message came from. What was forwarded is the message's own text and attachments.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `from_title` | `string` | type default | omit when `String::is_empty` is true |
| | | | The conversation it was first said in: `#announcements`, a person's name. |
| `from_space` | `string` | type default | omit when `String::is_empty` is true |
| | | | That conversation's Space, when it has one and it is not this one. |
| `link` | `string` | type default | omit when `String::is_empty` is true |
| | | | Opens the original in the network's own app. Empty when it cannot be linked to. |

## Group

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

A collapsible header inside a Space: a category, a sidebar section.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `id` | `string` | **error** | emit normally |
| `name` | `string` | **error** | emit normally |
| `position` | `int32` | **error** | emit normally |
| `collapsed` | `boolean` | type default | omit when `is_false` is true |
| | | | Remembered by chatd, never sent to the network. |
| `kind` | `GroupKind` | type default | omit when `GroupKind::is_section` is true |
| `count` | `uint32` | type default | omit when `is_zero` is true |
| | | | How many conversations sit under it, whatever page of them an answer carries. Filled by chatd on `Tree`; an adapter leaves it 0. |
| `muted` | `boolean` | type default | omit when `is_false` is true |
| | | | Muted on the network (a muted category): it starts collapsed. |
| `unread_only` | `boolean` | type default | omit when `is_false` is true |
| | | | The user's own "unread only" for this section (Slack): rows with nothing unread are not drawn, except the open one and starred ones. |

## GroupKind

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### section

Default variant for this type.

A category or sidebar section of channels.

JSON value: `"section"`.

No payload fields.

### directs

The direct and group conversations of a Space whose network keeps them inside it (a Slack workspace). Its rows are `Direct` and `Group` conversations with `space` set.

JSON value: `"directs"`.

No payload fields.

## InboxCounts

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

How many rows each Inbox filter holds, for the same `network` as the request.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `all` | `uint32` | **error** | emit normally |
| `unread` | `uint32` | **error** | emit normally |
| `mentions` | `uint32` | **error** | emit normally |
| `apps` | `uint32` | type default | omit when `is_zero` is true |
| | | | Bot and app rows with something unread: the Apps row's dot, never a number. |

## InboxFilter

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### all

Default variant for this type.

JSON value: `"all"`.

No payload fields.

### unread

Anything unread or mentioning me that is not muted: what I have not seen.

JSON value: `"unread"`.

No payload fields.

### mentions

Only what mentions me, muted or not: who is waiting on me.

JSON value: `"mentions"`.

No payload fields.

### directs

Direct and group conversations only.

JSON value: `"directs"`.

No payload fields.

## Key

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

Names a conversation, a Space or a person: the account it belongs to and the network's own id. Which of the three it is follows from the field it is in.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `network` | `Network` | **error** | emit normally |
| `account` | `string` | **error** | emit normally |
| `id` | `string` | **error** | emit normally |

## Keychain

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

What chatd is doing with the keychain. Sessions are read after the socket is answering, one network at a time; macOS may put up a prompt during a read.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `reading` | `boolean` | type default | omit when `is_false` is true |
| | | | The sessions are still being read; accounts appear as each network's is. |
| `waiting` | `nullable<Network>` | type default | omit when `Option::is_none` is true |
| | | | A read has gone on for over a second: macOS is asking the user. Shown as "Waiting for permission to read your sign-in from the keychain". |
| `denied` | `list<Network>` | type default | omit when `Vec::is_empty` is true |
| | | | Networks whose session could not be read: the prompt was denied or cancelled, or the keychain is locked. Their accounts and cache are kept; `ReadSessions` asks again. |

## Link

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### signed_out

No session. This is the default until the user signs in.

JSON value: `"signed_out"`.

No payload fields.

### expired

The network ended the session. What is cached stays readable; sending is refused until the user signs in again.

JSON value: `"expired"`.

No payload fields.

### offline

Signed in, but the socket is down or still connecting. `AccountStatus::reconnecting` says whether chatd is trying right now.

JSON value: `"offline"`.

No payload fields.

### connected

JSON value: `"connected"`.

No payload fields.

## Mark

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

The one tag after a name. Scam and Fake are drawn in `danger` wherever the name is.

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### verified

JSON value: `"verified"`.

No payload fields.

### scam

JSON value: `"scam"`.

No payload fields.

### fake

JSON value: `"fake"`.

No payload fields.

### guest

A guest of this workspace or tenant.

JSON value: `"guest"`.

No payload fields.

### external

From another organization (Slack Connect, a Teams federated user, a shared channel).

JSON value: `"external"`.

No payload fields.

### deactivated

The account was deactivated: drawn greyed, never in People.

JSON value: `"deactivated"`.

No payload fields.

## Media

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### stopped

mediad is not running. Calls and screen share are impossible in this state.

JSON value: `"stopped"`.

No payload fields.

### running

JSON value: `"running"`.

No payload fields.

## MediaFile

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/message.rs).

A file chatd can put on disk. The socket carries the path, never the bytes, and chatd never decodes it. `width` and `height` are known before the bytes arrive, so rows never jump.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `id` | `string` | **error** | emit normally |
| | | | Unique within the account and stable: an attachment id, or the network's avatar hash. A changed picture is a new id. |
| `kind` | `MediaKind` | **error** | emit normally |
| `width` | `uint32` | type default | omit when `is_zero` is true |
| | | | Pixels. 0 when the network did not say. |
| `height` | `uint32` | type default | omit when `is_zero` is true |
| `bytes` | `uint64` | type default | emit normally |
| | | | Size of the file. 0 when unknown. |
| `path` | `nullable<string>` | type default | omit when `Option::is_none` is true |
| | | | Where the file is, once it is on disk. `None`: ask `Fetch` when it is on screen. |
| `failed` | `nullable<string>` | type default | omit when `Option::is_none` is true |
| | | | Why the file could not be fetched, in plain words. While this is set chatd does not try again and the shell should stop asking; `Fetch` with `retry` clears it. |

## MediaKind

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/message.rs).

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### avatar

A person's or group's picture, at list size.

JSON value: `"avatar"`.

No payload fields.

### icon

A Space's icon.

JSON value: `"icon"`.

No payload fields.

### emoji

A custom emoji.

JSON value: `"emoji"`.

No payload fields.

### image

A still picture: an image, or the poster of a video or GIF, no wider than 800 px.

JSON value: `"image"`.

No payload fields.

### video

JSON value: `"video"`.

No payload fields.

### gif

JSON value: `"gif"`.

No payload fields.

### audio

JSON value: `"audio"`.

No payload fields.

### file

Anything else. Fetched only when the user asks.

JSON value: `"file"`.

No payload fields.

## MediaRequest

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/call.rs).

chatd to mediad, over mediad's stdin. Closing stdin ends the call. Each request gets exactly one reply (`Streams`, `Done` or `Refused`), in order.

Internally tagged object: discriminator `media`.

### streams

Discriminator: `"media": "streams"`.

No payload fields.

### share_send

Send our screen, or stop sending it.

Discriminator: `"media": "share_send"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `on` | `boolean` | **error** | emit normally |

### share_watch

Watch one participant's share. Replaces any share already being watched.

Discriminator: `"media": "share_watch"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `source` | `nullable<string>` | null | emit normally |

### speaker

The active speaker changed. Replaces the previous speaker's decode.

Discriminator: `"media": "speaker"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `source` | `nullable<string>` | null | emit normally |

### join

Connect the voice session. Progress and the outcome arrive as events.

Discriminator: `"media": "join"`.

Payload is `VoiceJoin`; merge its object/discriminator fields into this object, without a wrapper field.

### rejoin

The network moved a call that is already joined (a new voice server, a new session): drop the old connection and connect this one, keeping devices, mute and the call itself. Answered `Done`; then `Interrupted` and `Connected` as for any reconnect.

Discriminator: `"media": "rejoin"`.

Payload is `VoiceJoin`; merge its object/discriminator fields into this object, without a wrapper field.

### meter

The device menu opened or closed. While on, `Levels` are wanted and `DeviceList` is sent once at once and again whenever the system's devices change.

Discriminator: `"media": "meter"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `on` | `boolean` | **error** | emit normally |

### audio

Muted: capture nothing and send nothing. Deafened: play nothing.

Discriminator: `"media": "audio"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `muted` | `boolean` | **error** | emit normally |
| `deafened` | `boolean` | **error** | emit normally |

### devices

Device names as the system lists them. `None` follows the system default.

Discriminator: `"media": "devices"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `input` | `nullable<string>` | null | emit normally |
| `output` | `nullable<string>` | null | emit normally |

### tune

Gains, the speech gate and which cues play (Settings › Sounds and Audio & video). Sent at start and whenever one changes.

Discriminator: `"media": "tune"`.

Payload is `Tuning`; merge its object/discriminator fields into this object, without a wrapper field.

### cue

Plays one cue now, on the call's speaker, under the voices. Outside a call (a test mediad) it opens the speaker for the cue alone.

Discriminator: `"media": "cue"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `cue` | `Cue` | **error** | emit normally |

## MediaResponse

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/call.rs).

mediad to chatd, over mediad's stdout. `Ready` is sent once at start. `Streams`, `Done` and `Refused` answer a request; everything else is an event and may arrive at any time.

Internally tagged object: discriminator `media`.

### ready

Discriminator: `"media": "ready"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `engine_linked` | `boolean` | **error** | emit normally |

### streams

Discriminator: `"media": "streams"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `video` | `list<VideoStream>` | **error** | emit normally |

### done

Discriminator: `"media": "done"`.

No payload fields.

### refused

This mediad cannot do what was asked.

Discriminator: `"media": "refused"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `detail` | `string` | **error** | emit normally |

### connected

Voice is up both ways: the network accepted us and the transport is encrypted.

Discriminator: `"media": "connected"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `ssrc` | `uint32` | **error** | emit normally |
| | | | Our own audio SSRC. |
| `dave_version` | `uint16` | **error** | emit normally |
| | | | The end-to-end protocol version in use. 0 is none. |

### source

Whose audio an SSRC carries, as the voice gateway announced it.

Discriminator: `"media": "source"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `user_id` | `string` | **error** | emit normally |
| `ssrc` | `uint32` | **error** | emit normally |

### speaking

Someone is heard, or stopped. Our own `user_id` (the one in `VoiceJoin`) reports us.

Discriminator: `"media": "speaking"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `user_id` | `string` | **error** | emit normally |
| `speaking` | `boolean` | **error** | emit normally |

### gone

The voice gateway said this user left the connection.

Discriminator: `"media": "gone"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `user_id` | `string` | **error** | emit normally |

### levels

Our microphone's level and the mix being played, 0 to 100. At most ten a second, only while they change, and only while `Meter` is on.

Discriminator: `"media": "levels"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `input` | `uint8` | **error** | emit normally |
| `output` | `uint8` | **error** | emit normally |

### devices

The devices in use, at start and whenever the system moves them.

Discriminator: `"media": "devices"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `input` | `string` | **error** | emit normally |
| `output` | `string` | **error** | emit normally |

### device_list

Every device the system lists, by the names `MediaRequest::Devices` takes. Sent at start, when `Meter` turns on, and whenever one is plugged in or removed.

Discriminator: `"media": "device_list"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `inputs` | `list<string>` | **error** | emit normally |
| `outputs` | `list<string>` | **error** | emit normally |

### interrupted

Media stopped and mediad is reconnecting on its own.

Discriminator: `"media": "interrupted"`.

No payload fields.

### failed

The call cannot go on. mediad exits after sending this.

Discriminator: `"media": "failed"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `reason` | `CallFailure` | **error** | emit normally |
| `detail` | `string` | **error** | emit normally |

## MemberSection

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

One section of a member list, with how many people it holds on the network.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `name` | `string` | **error** | emit normally |
| `count` | `uint32` | **error** | emit normally |

## MentionKind

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/message.rs).

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### user

JSON value: `"user"`.

No payload fields.

### channel

JSON value: `"channel"`.

No payload fields.

### role

JSON value: `"role"`.

No payload fields.

### everyone

Everyone, here, channel.

JSON value: `"everyone"`.

No payload fields.

## Message

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/message.rs).

One message. Which conversation it is in comes from the answer that carries it.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `id` | `string` | **error** | emit normally |
| `sender` | `Sender` | **error** | emit normally |
| `sent` | `int64` | **error** | emit normally |
| | | | Unix seconds. |
| `outgoing` | `boolean` | type default | omit when `is_false` is true |
| `text` | `string` | type default | omit when `String::is_empty` is true |
| | | | Plain text. Mentions already read as names and no network markup is left in it. |
| `spans` | `list<Span>` | type default | omit when `Vec::is_empty` is true |
| `attachments` | `list<Attachment>` | type default | omit when `Vec::is_empty` is true |
| `previews` | `list<Preview>` | type default | omit when `Vec::is_empty` is true |
| `reactions` | `list<Reaction>` | type default | omit when `Vec::is_empty` is true |
| `reply_to` | `nullable<ReplyTo>` | type default | omit when `Option::is_none` is true |
| `thread` | `nullable<ThreadSummary>` | type default | omit when `Option::is_none` is true |
| `forwarded` | `nullable<Forwarded>` | type default | omit when `Option::is_none` is true |
| | | | Boxed, like `card`: few messages have one, and every message would carry its size. |
| `card` | `nullable<Card>` | type default | omit when `Option::is_none` is true |
| `deleted` | `boolean` | type default | omit when `is_false` is true |
| | | | A message that was deleted but still has a thread hanging off it. Everything it said is gone; the row stays so the thread has somewhere to hang. |
| `edited` | `boolean` | type default | omit when `is_false` is true |
| `pinned` | `boolean` | type default | omit when `is_false` is true |
| `mentions_me` | `boolean` | type default | omit when `is_false` is true |
| `kind` | `MessageKind` | type default | omit when `MessageKind::is_normal` is true |
| `state` | `SendState` | type default | omit when `SendState::is_sent` is true |
| `client_id` | `nullable<string>` | type default | omit when `Option::is_none` is true |
| | | | What the shell called it when sending. Set on our own messages only. |

## MessageHit

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

One hit of a message search: where the message is, and enough of it to choose by.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `Key` | **error** | emit normally |
| `message_id` | `string` | **error** | emit normally |
| | | | The message's id, to land on it with `Page::Around`. |
| `sent` | `int64` | **error** | emit normally |
| | | | Unix seconds. |
| `sender` | `string` | **error** | emit normally |
| | | | Who sent it, as the message's own row says. |
| `snippet` | `string` | **error** | emit normally |
| | | | The text around the match, on one line, at most 200 characters. |
| `title` | `string` | type default | omit when `String::is_empty` is true |
| | | | The conversation's title, so a result row says where it is without a second request. |
| `outgoing` | `boolean` | type default | omit when `is_false` is true |
| | | | Mine, so the row can say "You". |

## MessageKind

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/message.rs).

Internally tagged object: discriminator `kind`.

### normal

Default variant for this type.

Discriminator: `"kind": "normal"`.

No payload fields.

### system

One grey line: joined, pinned, call started. `text` says it.

Discriminator: `"kind": "system"`.

No payload fields.

### unsupported

Something tinyclient cannot draw. `text` names it ("Poll: Lunch?") and `link` opens it in the official app. Never blank, never dropped.

Discriminator: `"kind": "unsupported"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `link` | `string` | type default | omit when `String::is_empty` is true |

## Network

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### telegram

JSON value: `"telegram"`.

No payload fields.

### discord

JSON value: `"discord"`.

No payload fields.

### slack

JSON value: `"slack"`.

No payload fields.

### teams

JSON value: `"teams"`.

No payload fields.

### signal

JSON value: `"signal"`.

No payload fields.

### messages

Android Messages: Google Messages on the phone, paired to this computer.

JSON value: `"messages"`.

No payload fields.

## NetworkStatus

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

A network as a whole: the best link of its accounts, `SignedOut` when it has none.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `network` | `Network` | **error** | emit normally |
| `link` | `Link` | **error** | emit normally |

## Notify

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

How much of a conversation notifies the user. The network's own setting.

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### all

Default variant for this type.

JSON value: `"all"`.

No payload fields.

### mentions

JSON value: `"mentions"`.

No payload fields.

### nothing

Muted.

JSON value: `"nothing"`.

No payload fields.

## Occupant

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

Someone in a voice channel, as its row in the tree shows them.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `person` | `Key` | **error** | emit normally |
| `name` | `string` | **error** | emit normally |
| `muted` | `boolean` | type default | omit when `is_false` is true |
| `deafened` | `boolean` | type default | omit when `is_false` is true |
| `streaming` | `boolean` | type default | omit when `is_false` is true |
| | | | Sharing a screen or a camera. |

## Occupants

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

Who is in a voice channel, whether or not we are. Never stored: it arrives as `Change::Occupants` and rides on the row when the row is read.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `people` | `list<Occupant>` | **error** | emit normally |
| | | | At most `OCCUPANTS_LIMIT`, in the network's order. We are in it when we are in the channel. |
| `total` | `uint32` | **error** | emit normally |
| | | | How many are in the channel in all. |

## Outgoing

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

What a `Send` carries besides its text. All of it is off by default, and a plain text message leaves it off the wire.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `files` | `list<OutgoingFile>` | type default | omit when `Vec::is_empty` is true |
| | | | At most `ATTACHMENTS_LIMIT`, and at most the account's `Capabilities::max_files`. |
| `silent` | `boolean` | type default | omit when `is_false` is true |
| | | | Deliver without a notification (Discord's `@silent`, Telegram's silent). |
| `suppress_embeds` | `boolean` | type default | omit when `is_false` is true |
| | | | Ask the network not to unfurl the links in it. |
| `ping` | `boolean` | true | omit when `is_true` is true |
| | | | With `reply_to`: notify its author. On by default. |
| `pick` | `nullable<Pick>` | type default | omit when `Option::is_none` is true |
| `schedule` | `nullable<int64>` | type default | omit when `Option::is_none` is true |
| | | | Unix seconds: the network sends it then (Slack, Telegram). tinyclient never runs a timer that sends. |

## OutgoingFile

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

One file the user attached: the shell names a path on disk and chatd streams it from there. Bytes never cross the socket.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `path` | `string` | **error** | emit normally |
| `name` | `string` | type default | omit when `String::is_empty` is true |
| | | | The name the network shows. Empty: the path's file name. |
| `spoiler` | `boolean` | type default | omit when `is_false` is true |
| `as_file` | `boolean` | type default | omit when `is_false` is true |
| | | | Telegram: as a document, uncompressed. |
| `original` | `boolean` | type default | omit when `is_false` is true |
| | | | Send the file as it is (a HEIC rather than the JPEG made at staging). |

## Page

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

Which messages of a conversation. Always oldest first in the answer.

Internally tagged object: discriminator `at`.

### newest

Default variant for this type.

Discriminator: `"at": "newest"`.

No payload fields.

### before

Older than this message. When the cache runs out chatd asks the network and reports the arrival as a `Messages` change.

Discriminator: `"at": "before"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `id` | `string` | **error** | emit normally |

### after

Discriminator: `"at": "after"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `id` | `string` | **error** | emit normally |

### around

Centred on this message, which is included.

Discriminator: `"at": "around"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `id` | `string` | **error** | emit normally |

## Participant

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/call.rs).

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `id` | `string` | **error** | emit normally |
| | | | The person's id on the call's account. |
| `name` | `string` | **error** | emit normally |
| `speaking` | `boolean` | type default | emit normally |
| `muted` | `boolean` | type default | emit normally |
| `deafened` | `boolean` | type default | emit normally |

## Person

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `key` | `Key` | **error** | emit normally |
| `name` | `string` | **error** | emit normally |
| `handle` | `string` | type default | omit when `String::is_empty` is true |
| `avatar` | `nullable<MediaFile>` | type default | omit when `Option::is_none` is true |
| `bot` | `boolean` | type default | omit when `is_false` is true |
| `relation` | `Relation` | type default | emit normally |
| `presence` | `Presence` | type default | emit normally |
| `status` | `string` | type default | omit when `String::is_empty` is true |
| | | | Custom status text, as last seen. |
| `link` | `string` | type default | omit when `String::is_empty` is true |
| | | | Opens this person in the network's own app, where the network has such a link. |
| `emoji` | `string` | type default | omit when `String::is_empty` is true |
| | | | Their status's emoji, apart from its words (`status`). Live, like presence. |
| `activity` | `nullable<Activity>` | type default | omit when `Option::is_none` is true |
| | | | What they are doing now: playing, listening, in voice, in a meeting. Live. Boxed: few people in a list are doing anything. |
| `title` | `string` | type default | omit when `String::is_empty` is true |
| | | | Their job title (Slack, Teams). Stored. |
| `utc_offset` | `nullable<int32>` | type default | omit when `Option::is_none` is true |
| | | | Seconds east of UTC now, for "4:12 PM · 3 h behind you". Stored. |
| `mark` | `nullable<Mark>` | type default | omit when `Option::is_none` is true |

## Pick

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

A sticker or GIF chosen in the picker, sent as itself rather than uploaded.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `kind` | `CatalogKind` | **error** | emit normally |
| `id` | `string` | **error** | emit normally |
| | | | `CatalogItem::id`, which only the adapter understands. |

## PlayRequest

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/play.rs).

The shell to chatd: `Request::Play`. Each is answered `Ok` at once; what happens is told as `Change::Playback`.

Internally tagged object: discriminator `play`.

### start

Plays a file that is on disk (`path`, inside chatd's media cache), from `at` milliseconds, or from where it was paused. Whatever else was playing stops.

Discriminator: `"play": "start"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `account` | `AccountKey` | **error** | emit normally |
| `file` | `string` | **error** | emit normally |
| `path` | `string` | **error** | emit normally |
| `conversation` | `Key` | **error** | emit normally |
| `message` | `string` | **error** | emit normally |
| `title` | `string` | type default | omit when `String::is_empty` is true |
| `at` | `nullable<uint32>` | type default | omit when `Option::is_none` is true |
| `rate` | `uint16` | **error** | emit normally |
| `output` | `nullable<string>` | type default | omit when `Option::is_none` is true |
| | | | The speaker picked in the call menu. `None` follows the system default. |

### pause

Discriminator: `"play": "pause"`.

No payload fields.

### seek

Moves to `at` milliseconds, playing or paused.

Discriminator: `"play": "seek"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `at` | `uint32` | **error** | emit normally |

### rate

Discriminator: `"play": "rate"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `rate` | `uint16` | **error** | emit normally |

### stop

Stops and forgets it: the now-playing control goes.

Discriminator: `"play": "stop"`.

No payload fields.

## PlayState

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/play.rs).

Internally tagged object: discriminator `state`.

### loading

mediad is starting, opening the file and the speaker.

Discriminator: `"state": "loading"`.

No payload fields.

### playing

Discriminator: `"state": "playing"`.

No payload fields.

### paused

Discriminator: `"state": "paused"`.

No payload fields.

### ended

It played to the end. `at` is the end.

Discriminator: `"state": "ended"`.

No payload fields.

### failed

It cannot play, in plain words.

Discriminator: `"state": "failed"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `detail` | `string` | **error** | emit normally |

## Playback

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/play.rs).

The file that is playing, or was last played. Its position moves with the clock while `Playing`: `Playback::position`.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `account` | `AccountKey` | **error** | emit normally |
| `file` | `string` | **error** | emit normally |
| | | | The attachment's `MediaFile::id`. |
| `conversation` | `Key` | **error** | emit normally |
| | | | Where it was posted and who posted it, for the now-playing control. |
| `message` | `string` | **error** | emit normally |
| `title` | `string` | type default | omit when `String::is_empty` is true |
| `state` | `PlayState` | **error** | merge referenced object fields into parent; no field named state |
| `at` | `uint32` | **error** | emit normally |
| | | | Milliseconds into the file at `since`. |
| `since` | `uint64` | **error** | emit normally |
| | | | Unix milliseconds when `at` was true. |
| `duration` | `uint32` | type default | emit normally |
| | | | Milliseconds. 0 until mediad has read the file. |
| `rate` | `uint16` | **error** | emit normally |
| | | | Percent of normal speed: one of `RATES`. |

## PlayerEvent

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/play.rs).

`mediad --play` to chatd, over its stdout.

Internally tagged object: discriminator `player`.

### playing

Sound is leaving the speaker from `at` milliseconds, at `rate`: after opening, a seek and a change of speed.

Discriminator: `"player": "playing"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `at` | `uint32` | **error** | emit normally |
| `duration` | `uint32` | **error** | emit normally |
| `rate` | `uint16` | **error** | emit normally |

### ended

The end was played. mediad exits.

Discriminator: `"player": "ended"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `duration` | `uint32` | **error** | emit normally |

### stopped

stdin closed. Where it got to; mediad exits.

Discriminator: `"player": "stopped"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `at` | `uint32` | **error** | emit normally |

### failed

The file or the speaker could not be used. mediad exits.

Discriminator: `"player": "failed"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `detail` | `string` | **error** | emit normally |

## PlayerRequest

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/play.rs).

chatd to `mediad --play`, over its stdin. Closing stdin stops playing: mediad answers `Stopped` with where it got to, and exits.

Internally tagged object: discriminator `player`.

### open

Discriminator: `"player": "open"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `path` | `string` | **error** | emit normally |
| `at` | `uint32` | **error** | emit normally |
| `rate` | `uint16` | **error** | emit normally |
| `output` | `nullable<string>` | type default | omit when `Option::is_none` is true |

### seek

Discriminator: `"player": "seek"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `at` | `uint32` | **error** | emit normally |

### rate

Discriminator: `"player": "rate"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `rate` | `uint16` | **error** | emit normally |

## Presence

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

Never stored. Known only for people the shell is watching and for lists the user owns.

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### unknown

Default variant for this type.

Not offline: drawn as no dot at all.

JSON value: `"unknown"`.

No payload fields.

### online

JSON value: `"online"`.

No payload fields.

### idle

JSON value: `"idle"`.

No payload fields.

### dnd

JSON value: `"dnd"`.

No payload fields.

### busy

In a meeting, a call or a huddle (Teams' Busy): a solid red disc, distinct from do-not-disturb's bar.

JSON value: `"busy"`.

No payload fields.

### offline

JSON value: `"offline"`.

No payload fields.

## Preview

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/message.rs).

A link's card, as the network built it. tinyclient never fetches the link itself.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `url` | `string` | **error** | emit normally |
| `site` | `string` | type default | omit when `String::is_empty` is true |
| `title` | `string` | type default | omit when `String::is_empty` is true |
| `description` | `string` | type default | omit when `String::is_empty` is true |
| `image` | `nullable<MediaFile>` | type default | omit when `Option::is_none` is true |
| | | | Only when the network serves it from its own proxy. |

## Profile

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

What a person's card shows beyond the row: asked for one person at a time, never stored.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `person` | `Person` | **error** | emit normally |
| `bio` | `string` | type default | omit when `String::is_empty` is true |
| | | | Their own words about themselves, cut to 1,000 characters. |
| `mutual_spaces` | `list<string>` | type default | omit when `Vec::is_empty` is true |
| | | | The titles of the Spaces we share, at most `MUTUAL_SPACES`. |
| `time_zone` | `string` | type default | omit when `String::is_empty` is true |
| | | | Their time zone as the network names it (`Europe/Lisbon`), and its offset from UTC in seconds now, so the shell can show their local time without a zone database. |
| `utc_offset` | `nullable<int32>` | type default | omit when `Option::is_none` is true |
| `fields` | `list<tuple(string,string)>` | type default | omit when `Vec::is_empty` is true |
| | | | What else the network says of them that has no typed place below, as label and value in its own words. At most `PROFILE_FIELDS`. Leftovers only: the shell draws them last. |
| `since` | `nullable<int64>` | type default | omit when `Option::is_none` is true |
| | | | Unix seconds they joined the network ("Member since"). |
| `mutual_friends` | `uint32` | type default | omit when `is_zero` is true |
| | | | Friends we have in common, where the network counts them. |
| `accent` | `nullable<uint32>` | type default | omit when `Option::is_none` is true |
| | | | The colour of their profile's banner, `0xRRGGBB`, and its picture where they set one. |
| `banner` | `nullable<MediaFile>` | type default | omit when `Option::is_none` is true |
| `nickname` | `string` | type default | omit when `String::is_empty` is true |
| | | | Their nickname in the Space the card was opened from (`Profile.space`). |
| `pronouns` | `string` | type default | omit when `String::is_empty` is true |
| `title` | `string` | type default | omit when `String::is_empty` is true |
| `department` | `string` | type default | omit when `String::is_empty` is true |
| `roles` | `list<string>` | type default | omit when `Vec::is_empty` is true |
| | | | Their roles in that Space, names only (colours are left out), at most `PROFILE_ROLES`. |
| `contacts` | `list<Contact>` | type default | omit when `Vec::is_empty` is true |
| | | | Email and phone, each copied on click; phone numbers masked until clicked. At most `PROFILE_CONTACTS`. |
| `mutual_total` | `uint32` | type default | omit when `is_zero` is true |
| | | | How many Spaces we share in all, when that is more than `mutual_spaces` lists. |
| `joined` | `nullable<int64>` | type default | omit when `Option::is_none` is true |
| | | | Unix seconds: joined that Space, became friends, last seen online. |
| `friends_since` | `nullable<int64>` | type default | omit when `Option::is_none` is true |
| `last_seen` | `nullable<int64>` | type default | omit when `Option::is_none` is true |
| `status_until` | `nullable<int64>` | type default | omit when `Option::is_none` is true |
| | | | When their status clears, unix seconds. |
| `away` | `string` | type default | omit when `String::is_empty` is true |
| | | | Out of office, in the network's words, and until when. |
| `away_until` | `nullable<int64>` | type default | omit when `Option::is_none` is true |
| `note` | `string` | type default | omit when `String::is_empty` is true |
| | | | The user's own private note on them. |
| `warning` | `nullable<Warning>` | type default | omit when `Option::is_none` is true |

## Reaction

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/message.rs).

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `emoji` | `string` | **error** | emit normally |
| | | | The emoji itself, or `:name:` for a custom one. |
| `file` | `nullable<MediaFile>` | type default | omit when `Option::is_none` is true |
| `count` | `uint32` | **error** | emit normally |
| `mine` | `boolean` | type default | omit when `is_false` is true |

## ReactionRules

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/react.rs).

What one conversation takes as reactions from this account. The default is what a network that never said anything is taken to allow: any emoji, no limits.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `set` | `ReactionSet` | type default | omit when `is_any` is true |
| `only` | `list<string>` | type default | omit when `Vec::is_empty` is true |
| | | | With `Only`: the emoji allowed, in the network's order, spelled as `React` sends them. A custom one is named by its registered file's id. |
| `tones` | `boolean` | type default | omit when `is_false` is true |
| | | | A listed emoji may be given in a skin tone too (Slack, Teams), not only as listed. |
| `custom` | `EmojiScope` | type default | omit when `EmojiScope::is_none` is true |
| | | | Which of the account's custom emoji (`Catalog` with `Emoji`) may be chosen here. |
| `animated` | `boolean` | type default | omit when `is_false` is true |
| | | | Animated custom emoji may be chosen too (Discord: Nitro only). |
| `join` | `boolean` | true | omit when `is_true` is true |
| | | | A reaction already on a message may be added to even when it could not be chosen here: Discord lets anyone join another server's emoji. False on Telegram, where a reaction the chat no longer allows cannot be given again. |
| `join_only` | `boolean` | type default | omit when `is_false` is true |
| | | | Only reactions already on a message may be added to (Discord without Add Reactions). |
| `mine` | `uint32` | type default | omit when `is_zero` is true |
| | | | Most of my reactions on one message. 0: no limit. |
| `replaces` | `boolean` | type default | omit when `is_false` is true |
| | | | At `mine`, a new one takes the place of my oldest (Telegram, Signal) instead of being refused. |
| `distinct` | `uint32` | type default | omit when `is_zero` is true |
| | | | Most different emoji one message holds. 0: no limit. |
| `why` | `string` | type default | omit when `String::is_empty` is true |
| | | | Why reactions are off, in words, when `set` is `Off`. |

## ReactionSet

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/react.rs).

Which emoji may be chosen as a new reaction.

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### any

Default variant for this type.

Every Unicode emoji (Discord, Slack, Signal).

JSON value: `"any"`.

No payload fields.

### only

Only those in `ReactionRules::only` (a Telegram chat's set, Teams' catalog).

JSON value: `"only"`.

No payload fields.

### off

None: reactions are off here, and `ReactionRules::why` says so.

JSON value: `"off"`.

No payload fields.

## RelateAction

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

What the user does about a person. Never automated: only on a shell request.

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### accept

Accept their friend request.

JSON value: `"accept"`.

No payload fields.

### ignore

Dismiss their friend request without telling them.

JSON value: `"ignore"`.

No payload fields.

### cancel

Withdraw the request I sent.

JSON value: `"cancel"`.

No payload fields.

### remove

End the friendship.

JSON value: `"remove"`.

No payload fields.

### block

JSON value: `"block"`.

No payload fields.

## Relation

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### none

Default variant for this type.

Seen somewhere: a message author, a search result.

JSON value: `"none"`.

No payload fields.

### contact

Someone I have a direct conversation with, on networks that have no friends.

JSON value: `"contact"`.

No payload fields.

### friend

JSON value: `"friend"`.

No payload fields.

### incoming

They asked to be my friend.

JSON value: `"incoming"`.

No payload fields.

### outgoing

I asked.

JSON value: `"outgoing"`.

No payload fields.

### blocked

JSON value: `"blocked"`.

No payload fields.

## ReplyTo

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/message.rs).

The earlier message this one answers, as one line.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `id` | `string` | **error** | emit normally |
| `sender` | `string` | **error** | emit normally |
| `snippet` | `string` | **error** | emit normally |
| `person` | `nullable<Key>` | type default | omit when `Option::is_none` is true |
| | | | Who wrote it, for their picture. `None` for a webhook, or when the network did not say. |
| `deleted` | `boolean` | type default | omit when `is_false` is true |
| | | | The message answered has been deleted. `snippet` is then empty. |

## SendState

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/message.rs).

Internally tagged object: discriminator `state`.

### sent

Default variant for this type.

On the network. Every incoming message is this.

Discriminator: `"state": "sent"`.

No payload fields.

### pending

On its way. The message's `id` is its `client_id` until the network names it.

Discriminator: `"state": "pending"`.

No payload fields.

### failed

It did not go, and will not unless the user asks. `reason` is in words.

Discriminator: `"state": "failed"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `reason` | `string` | **error** | emit normally |

## Sender

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/message.rs).

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `id` | `string` | type default | omit when `String::is_empty` is true |
| | | | The person's id on the account. Empty for a webhook or an app with no user. |
| `name` | `string` | **error** | emit normally |
| `avatar` | `nullable<MediaFile>` | type default | omit when `Option::is_none` is true |
| `bot` | `boolean` | type default | omit when `is_false` is true |

## SharedItem

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

One thing shared in a conversation, and the message it was shared in.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `message_id` | `string` | **error** | emit normally |
| `sent` | `int64` | **error** | emit normally |
| | | | Unix seconds. |
| `sender` | `string` | **error** | emit normally |
| `attachment` | `nullable<Attachment>` | type default | omit when `Option::is_none` is true |
| | | | For `Media` and `Files`. |
| `url` | `string` | type default | omit when `String::is_empty` is true |
| | | | For `Links`: where it goes, and the page's title when the network made a preview. |
| `title` | `string` | type default | omit when `String::is_empty` is true |

## SharedKind

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

Which of the things said in a conversation `Shared` lists.

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### media

Pictures, videos and GIFs.

JSON value: `"media"`.

No payload fields.

### files

Every other attachment: documents, archives, audio.

JSON value: `"files"`.

No payload fields.

### links

JSON value: `"links"`.

No payload fields.

## Shelf

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

Which list of a network's home `Home` reads.

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### main

Default variant for this type.

The chats: neither archived nor requests.

JSON value: `"main"`.

No payload fields.

### archive

The network's archive (Telegram).

JSON value: `"archive"`.

No payload fields.

### requests

Message requests from strangers (Discord): never counted, opening one reads nothing.

JSON value: `"requests"`.

No payload fields.

## SignInInput

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/signin.rs).

What the user did about a step.

Internally tagged object: discriminator `input`.

### use_qr

Scan a code instead of typing a number.

Discriminator: `"input": "use_qr"`.

No payload fields.

### use_phone

Type a number instead of scanning.

Discriminator: `"input": "use_phone"`.

No payload fields.

### phone

Discriminator: `"input": "phone"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `number` | `string` | **error** | emit normally |

### code

Discriminator: `"input": "code"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `code` | `string` | **error** | emit normally |

### password

Discriminator: `"input": "password"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `password` | `string` | **error** | emit normally |

### resend

Send the code again, the way `SignInStep::Code::next` says.

Discriminator: `"input": "resend"`.

No payload fields.

### back

One step back: from the code to the number, from the number to the QR code.

Discriminator: `"input": "back"`.

No payload fields.

## SignInProblem

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/signin.rs).

Why the step is being shown again. The shell has the words for each.

Internally tagged object: discriminator `problem`.

### unreachable

The network could not be reached.

Discriminator: `"problem": "unreachable"`.

No payload fields.

### phone_invalid

Discriminator: `"problem": "phone_invalid"`.

No payload fields.

### phone_unknown

No account uses this number, and tinyclient does not create accounts.

Discriminator: `"problem": "phone_unknown"`.

No payload fields.

### phone_banned

Discriminator: `"problem": "phone_banned"`.

No payload fields.

### code_invalid

Discriminator: `"problem": "code_invalid"`.

No payload fields.

### code_expired

Discriminator: `"problem": "code_expired"`.

No payload fields.

### password_invalid

Discriminator: `"problem": "password_invalid"`.

No payload fields.

### too_many

The network will not take another try before `until` (unix seconds).

Discriminator: `"problem": "too_many"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `until` | `int64` | **error** | emit normally |

### other

Anything else, in words the user can read.

Discriminator: `"problem": "other"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `reason` | `string` | **error** | emit normally |

## SignInStep

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/signin.rs).

Where a sign-in stands: what the shell draws now.

Internally tagged object: discriminator `step`.

### qr

Scan `link` as a QR code with the network's phone app. Empty until the network has issued one. The network replaces it at `expires` (unix seconds); the new one is a `Change`.

Discriminator: `"step": "qr"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `link` | `string` | type default | omit when `String::is_empty` is true |
| `expires` | `int64` | type default | emit normally |
| `problem` | `nullable<SignInProblem>` | type default | omit when `Option::is_none` is true |

### phone

Ask for the phone number, in international form.

Discriminator: `"step": "phone"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `problem` | `nullable<SignInProblem>` | type default | omit when `Option::is_none` is true |

### code

A code of `length` digits was sent `via`, for the number `phone` as the user typed it.

Discriminator: `"step": "code"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `via` | `CodeVia` | **error** | emit normally |
| `length` | `uint8` | **error** | emit normally |
| `phone` | `string` | type default | omit when `String::is_empty` is true |
| `next` | `nullable<CodeVia>` | type default | omit when `Option::is_none` is true |
| | | | How `Resend` would send it, when the network offers another way. |
| `resend_at` | `int64` | type default | emit normally |
| | | | Unix seconds before which `Resend` is refused. 0: any time. |
| `problem` | `nullable<SignInProblem>` | type default | omit when `Option::is_none` is true |

### password

The account has a second password. `hint` is the user's own, as the network keeps it.

Discriminator: `"step": "password"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `hint` | `string` | type default | omit when `String::is_empty` is true |
| `problem` | `nullable<SignInProblem>` | type default | omit when `Option::is_none` is true |

### done

Signed in. The account is in `Status` from now on.

Discriminator: `"step": "done"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `account` | `nullable<AccountKey>` | type default | omit when `Option::is_none` is true |

### failed

It cannot go on. `reason` is in words; beginning again starts over.

Discriminator: `"step": "failed"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `reason` | `string` | **error** | emit normally |

## Space

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

A server, workspace or team. Every account also has its direct conversations, which belong to no Space.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `key` | `Key` | **error** | emit normally |
| `name` | `string` | **error** | emit normally |
| `icon` | `nullable<MediaFile>` | type default | omit when `Option::is_none` is true |
| `position` | `int32` | **error** | emit normally |
| | | | The network's own order. |
| `attention` | `uint32` | **error** | emit normally |
| `unread` | `boolean` | **error** | emit normally |
| `folder` | `nullable<string>` | type default | omit when `Option::is_none` is true |
| | | | The folder it is filed in (Discord's server folders), by `Folder::key` id. |
| `muted` | `boolean` | type default | omit when `is_false` is true |
| | | | Muted as a whole: every row in it is drawn dimmed. |
| `hide_muted` | `boolean` | type default | omit when `is_false` is true |
| | | | The user's own "hide muted channels" for this Space: muted rows with nothing for me are not drawn in its tree. |

## SpaceInfo

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

A Space's info: opened from its name, never from a conversation.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `space` | `Space` | **error** | emit normally |
| `description` | `string` | type default | omit when `String::is_empty` is true |
| `members` | `nullable<uint32>` | type default | omit when `Option::is_none` is true |
| `online` | `nullable<uint32>` | type default | omit when `Option::is_none` is true |
| `nickname` | `string` | type default | omit when `String::is_empty` is true |
| | | | Our own nickname and roles there, role colours left out. |
| `roles` | `list<string>` | type default | omit when `Vec::is_empty` is true |
| `notify` | `Notify` | type default | emit normally |

## Span

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/message.rs).

A styled range of `Message::text`. `start` and `end` are byte offsets into the UTF-8 text and always fall on character boundaries. Ranges may nest and overlap.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `start` | `uint32` | **error** | emit normally |
| `end` | `uint32` | **error** | emit normally |
| `style` | `Style` | **error** | emit normally |

## Special

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

What a conversation is besides its kind. Each changes what the row may do.

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### none

Default variant for this type.

JSON value: `"none"`.

No payload fields.

### saved

The user's own notes: Telegram's Saved Messages, Teams' Notes, a Slack DM with oneself. No presence, no call.

JSON value: `"saved"`.

No payload fields.

### service

The network's own account: Telegram's 777000 (login codes), Discord's system DMs. Read-only, never a call, never muted by tinyclient.

JSON value: `"service"`.

No payload fields.

### request

A message request from a stranger. Listed only behind the Requests row, never counted, and opening it reads nothing on the network.

JSON value: `"request"`.

No payload fields.

## Style

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/message.rs).

How a range of a message's text is drawn. Block styles (`CodeBlock`, `Quote`, `ListItem`) cover whole lines.

Internally tagged object: discriminator `style`.

### bold

Discriminator: `"style": "bold"`.

No payload fields.

### italic

Discriminator: `"style": "italic"`.

No payload fields.

### underline

Discriminator: `"style": "underline"`.

No payload fields.

### strike

Discriminator: `"style": "strike"`.

No payload fields.

### code

Discriminator: `"style": "code"`.

No payload fields.

### code_block

Discriminator: `"style": "code_block"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `language` | `string` | type default | omit when `String::is_empty` is true |

### quote

Discriminator: `"style": "quote"`.

No payload fields.

### list_item

Discriminator: `"style": "list_item"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `ordered` | `boolean` | **error** | emit normally |
| `depth` | `uint8` | **error** | emit normally |

### spoiler

Discriminator: `"style": "spoiler"`.

No payload fields.

### link

Discriminator: `"style": "link"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `url` | `string` | **error** | emit normally |

### mention

The text already reads `@Priya` or `#deploys`; `id` is who or what it names.

Discriminator: `"style": "mention"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `kind` | `MentionKind` | **error** | emit normally |
| `id` | `string` | **error** | emit normally |

### emoji

A custom emoji. The text reads `:name:`, which is also the fallback.

Discriminator: `"style": "emoji"`.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `file` | `MediaFile` | **error** | emit normally |

## ThreadSummary

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/message.rs).

The thread hanging off this message. Its replies are not in the conversation's own pages.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `id` | `string` | **error** | emit normally |
| | | | The thread's conversation id: what the thread pane asks `Messages` for. |
| `replies` | `uint32` | **error** | emit normally |
| `last` | `int64` | **error** | emit normally |
| | | | Unix seconds of the newest reply. |
| `participants` | `list<Key>` | type default | omit when `Vec::is_empty` is true |
| | | | The latest people to reply, newest first, at most `THREAD_FACES`, for their pictures. |
| `unread` | `uint32` | type default | omit when `is_zero` is true |
| | | | Replies the user has not read. 0 when the network does not say per thread. |

## Tuning

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/call.rs).

What the user chose for a call's sound. Percentages, 0 to 100.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `voice` | `uint8` | **error** | emit normally |
| | | | Everyone's voice in the mix. 100 is the level as decoded. |
| `gate` | `uint8` | **error** | emit normally |
| | | | Our microphone counts as speech from this level (`audio::level`) up. |
| `cues` | `uint8` | **error** | emit normally |
| | | | The cues' volume. At 100 a cue peaks at -20 dBFS. |
| `joins` | `boolean` | **error** | emit normally |
| | | | Someone joins or leaves (S7). |
| `mine` | `boolean` | **error** | emit normally |
| | | | I mute, unmute, deafen or undeafen (S8). |
| `connection` | `boolean` | **error** | emit normally |
| | | | The connection is lost or back (S9). |

## Typist

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

Someone typing in a conversation right now.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `id` | `string` | **error** | emit normally |
| `name` | `string` | **error** | emit normally |
| `until` | `int64` | **error** | emit normally |
| | | | Unix seconds at which the line goes away if nothing more is heard. The shell times this out itself; chatd sends no change for it. |

## VideoStream

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/call.rs).

A video stream mediad holds a codec session for.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `direction` | `Direction` | **error** | emit normally |
| `content` | `Content` | **error** | emit normally |
| `source` | `string` | **error** | emit normally |
| | | | Who the stream belongs to. Empty for our own encode. |

## VoiceJoin

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/call.rs).

Everything mediad needs to join one Discord voice connection. The adapter gathers it from the gateway (`VOICE_STATE_UPDATE` gives the session id, `VOICE_SERVER_UPDATE` the rest) and chatd passes it on untouched.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `network` | `Network` | **error** | emit normally |
| `endpoint` | `string` | **error** | emit normally |
| | | | Host and port of the voice gateway, without a scheme. |
| `token` | `string` | **error** | emit normally |
| `session_id` | `string` | **error** | emit normally |
| `user_id` | `string` | **error** | emit normally |
| `server_id` | `string` | **error** | emit normally |
| | | | The voice gateway's `server_id`: the guild, or the channel for a direct call. |
| `channel_id` | `string` | **error** | emit normally |
| `dave` | `Dave` | **error** | emit normally |
| `muted` | `boolean` | **error** | emit normally |
| `deafened` | `boolean` | **error** | emit normally |

## Warning

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/info.rs).

The one heads-up line on a profile.

Externally tagged enumeration: unit variants are JSON strings; data variants use a single-key object.

### scam

JSON value: `"scam"`.

No payload fields.

### fake

JSON value: `"fake"`.

No payload fields.

### spam

The network says impersonation or spam about this account.

JSON value: `"spam"`.

No payload fields.

## Watching

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).

What the shell has on screen. Replaces the previous `Watch` as a whole. chatd asks the network for presence, typing and members of exactly this and drops the rest. It lapses when the shell stops asking `Wait`.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `conversation` | `nullable<Key>` | type default | omit when `Option::is_none` is true |
| | | | The open conversation. |
| `people` | `list<Key>` | type default | omit when `Vec::is_empty` is true |
| | | | People whose presence is drawn, at most `WATCH_LIMIT`. |
| `members` | `nullable<tuple(uint32,uint32)>` | type default | omit when `Option::is_none` is true |
| | | | The rows of the open conversation's member list that are visible: first row and count. |
| `space` | `nullable<Key>` | type default | omit when `Option::is_none` is true |
| | | | The Space whose tree is on screen, whether or not a conversation of it is open. An adapter keeps a Space's live subscription only while it is named here. |
| `rows` | `list<Key>` | type default | omit when `Vec::is_empty` is true |
| | | | The conversation rows on screen in any list, at most `ROWS_WATCHED`. chatd fills in the preview of those that have none, paced, on every network but Discord. |

## settings::Setting

[Source](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/settings.rs).

One stored setting.

JSON object.

| Field | JSON type | Missing field | Serialization notes |
| --- | --- | --- | --- |
| `scope` | `string` | **error** | emit normally |
| | | | `""` global, `account:<network>:<id>`, or `conv:<network>:<account>:<id>`. |
| `key` | `string` | **error** | emit normally |
| `value` | `string` | **error** | emit normally |
