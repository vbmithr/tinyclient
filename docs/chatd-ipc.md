# Chatd IPC specification

This specifies the local TinyClient–chatd protocol at upstream commit
`7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91` (18 October 2026, version 0.2.5).
The Linux reconnect change in PR #45 does not change this wire protocol.

The intended reader is implementing a client or replacement daemon in another
language. **MUST** denotes a requirement for compatibility with this snapshot,
not a promise that future releases will keep it unchanged. The source currently
provides no separately versioned protocol or negotiated feature version.

Read this together with the [complete type catalogue](chatd-ipc-types.md), which
lists 94 serializable types, all 68 requests, all 30 responses, all 19 change
variants, field types, missing-field behavior and serialization omissions.
The catalogue also includes helper-process types; those are not additional
operations accepted on the chat socket.

## Transport and process discovery

On Unix, use a filesystem Unix-domain stream socket named `chat.sock` within the
support directory. There is no TCP listener, HTTP transport, TLS layer or
application authentication handshake in this protocol. Local filesystem access
and process supervision are part of the deployment boundary; a replacement
should not expose this interface to arbitrary remote clients.

The reference support-directory selection is:

| Platform | Directory, in precedence order |
| --- | --- |
| All | `TINYCLIENT_DIR`, when present |
| Linux/other Unix | `$XDG_DATA_HOME/tinyclient`, otherwise `$HOME/.local/share/tinyclient` |
| macOS | `$HOME/Library/Application Support/tinyclient` |
| Windows | `%APPDATA%/tinyclient`, then `%USERPROFILE%/AppData/Roaming/tinyclient`, then `C:\ProgramData\tinyclient` |

If HOME is absent on Unix, the reference uses `/tmp` as its home fallback.

Windows uses a named pipe, not a filesystem socket. Its current name is
`\\.\pipe\tinyclient-<16 lowercase hexadecimal digits>`. The suffix is produced
by hashing the logical `chat.sock` path's Rust `OsStr` with
`std::collections::hash_map::DefaultHasher::new()`. This is an implementation
detail rather than a portable published hash specification. A non-Rust Windows
implementation MUST reproduce both the path hashing inputs and algorithm for
the targeted build, or change discovery on both ends. Hashing UTF-8 with an
arbitrary hash function will not interoperate.

TinyClient tries `Ping` before starting a daemon. `TINYCLIENT_CHATD` selects an
alternative executable; otherwise it looks beside the GUI executable. On Linux,
an enabled user service is used for the default profile. An explicit executable
or scratch-directory override uses direct startup instead. An override does not
redirect an already running daemon: experiment with a separate `TINYCLIENT_DIR`.
The reference daemon holds an OS lock on `chatd.lock` for its lifetime. A drop-in
replacement MUST prevent two writers for the same profile and use compatible
locking semantics; merely creating a file with that name is insufficient.

## Framing and connection behavior

Each frame is a four-byte **unsigned big-endian** payload length followed by
exactly that many bytes of UTF-8 JSON. The length counts bytes, not characters,
and excludes the four-byte header. Maximum payload size is 1,048,576 bytes.
Frames are not newline-delimited; JSON whitespace is allowed within a payload.
There is no compression or request-ID header.

For example, `{"op":"ping"}` is 13 bytes, so its header is `00 00 00 0d`.
The answer is the equally framed JSON object `{"op":"pong"}`.

A connection can carry successive requests. The server processes them in order
and writes exactly one response per complete validly framed request. Responses
are correlated by order, not an ID. A client SHOULD keep at most one outstanding
request on a connection. A long `Wait` or sign-in blocks later requests on that
connection; concurrent operations require separate connections. There is no
unsolicited server push on the chat socket.

A receiver MUST handle partial reads and writes. EOF or a truncated frame ends
the connection. An input length over the limit closes the reference connection
without a structured error. A well-framed but invalid JSON/request object gets
an `error` response with code `unsupported`; the connection remains usable.
An answer that exceeds the limit is replaced with `error` / `too_large`.
A caught request-handler panic produces `error` / `internal`.

## JSON representation

Request and Response are objects discriminated by `op`; Change is discriminated
by `what`. Names are snake_case. Object key order is irrelevant. Numbers, booleans,
arrays and null MUST retain their JSON types: `"false"` is not false.

The type catalogue uses language-neutral names such as `uint64`, `list<Key>` and
`nullable<Key>`. Integer widths and signs are significant. Implementations using
floating-point JSON numbers MUST preserve unsigned 64-bit sequence values and
other integer fields exactly, including values above 2^53 when they occur.
IDs are strings, even when a service uses decimal-looking identifiers.

A missing non-nullable field is an error unless the catalogue gives a default.
A nullable field accepts null or omission. Serialization omits fields only under
the stated omission condition; otherwise the reference encoder emits the field,
including explicit null. Unknown object fields are normally ignored by the
reference decoder. Unknown enum variants are not: a new operation or state can
break an older decoder even when adding an optional field would not.

A nested newtype has no extra wrapper. For example, Request's `watch` payload is
Watching merged into the request object, not `{"watching": {...}}`:

```json
{"op":"watch","conversation":{"network":"discord","account":"1000","id":"4101"},"space":{"network":"discord","account":"1000","id":"4000"},"members":[0,50]}
```

Request's `play` and `media` likewise merge their payload enum's discriminator
and fields into the outer object. For example:

```json
{"op":"play","play":"pause"}
```

Fields marked **flatten** in the catalogue merge a referenced object's fields
into their containing object. Call.state and Playback.state are examples: their
state discriminator appears directly on the call/playback object.

## Identities and values

`AccountKey` is `{network, account}`. `Key` adds `id`; the field containing the
Key determines whether it denotes a conversation, person or Space. A Space is a
Discord server, Slack workspace or Teams team. A Slack sign-in can yield several
accounts. Keys MUST include the account: the same service ID alone is not enough.
Network values are `telegram`, `discord`, `slack`, `teams`, `signal`, `messages`.

`Message.sent` is Unix **seconds**. `Status.started` is Unix **milliseconds**.
Playback positions and several media controls use milliseconds; attachment
duration uses seconds. Read each field's catalogue description. Sequence numbers
are opaque cursors, not timestamps a client should interpret.

Text spans use **UTF-8 byte offsets**, not Unicode character indexes or UTF-16
code units. Their boundaries MUST fall on character boundaries; ranges can nest
or overlap. Message text is normalized display text rather than raw service
markup. Rich message kinds, attachments, replies and cards have typed payloads.

A `MediaFile` is a registered file descriptor object, not the file's bytes:
`{id, kind, ...}` with optional `path` and `failed`. Its ID is stable within its
account. A changed avatar can have a different file ID. Local paths are strings
interpreted on the same machine as the GUI.

## Defaults and omission

For `type default`, use false for boolean, zero for numbers, empty string/list
for strings/lists, null for nullable types, and the marked default variant for
enums. For structs, apply their field defaults. Important explicit defaults are:

- Outgoing: files `[]`, silent false, suppress_embeds false, **ping true**, pick
  null, schedule null. `Send.with` may be omitted for this plain-send value.
- ReactionRules: set `any`, only `[]`, tones false, custom `none`, animated false,
  **join true**, join_only false, mine 0, replaces false, distinct 0, why `""`.
- Tuning's programmatic default: voice 100, gate 25, cues 50, joins/mine/connection
  true. This does not make each field optional when decoding a Tuning object;
  its catalogue marks those fields required.
- Keychain: reading false, waiting null, denied `[]`; the whole Status.keychain
  field is omitted when this settled value applies.
- Capabilities: the all-default value disables optional send capabilities and
  uses zero numeric limits; AccountStatus.can omission does not mean unlimited support.
- Members.pending defaults false and is omitted when false.

The catalogue retains omission predicate names from the reference source.
`is_normal`, `is_sent`, `is_section`, `is_main`, `is_any` and `is_none` refer to
their named default enum variants. `Capabilities::is_none` and
`Keychain::is_settled` test equality with their complete default objects.

## Startup and change synchronization

A client starts with `Ping` and then `Status`. The daemon answers its local socket
before session restoration completes. A responsive daemon may therefore report
keychain work or offline accounts; `Pong` is not proof of network connectivity.

A structurally minimal Status response for an empty profile is:

```json
{"op":"status","networks":[],"accounts":[],"media":"stopped","call":null,"seq":42,"started":1792310400000}
```

A full implementation reports its network/account states; the empty arrays here
illustrate the wire shape, not the expected list of supported networks.

Save `Status.seq`, then issue `Wait {since: seq}` on a dedicated connection.
The reference waits up to 30 seconds. It returns `Changes {seq, reset, changes}`;
use that returned seq for the next Wait, including an empty timeout response.

```json
{"op":"wait","since":42}
```

```json
{"op":"changes","seq":42,"reset":false,"changes":[]}
```

The hub retains at most 256 changed scopes. Repeated updates to the same scope
can replace one another. This is an **invalidation feed**, not a durable event
log: the client cannot infer that it saw every intermediate event.

When `reset` is true, discard incremental assumptions and reread the currently
visible snapshots. `Status.started` changing also means the daemon restarted.
A cursor older than the retained floor or greater than the current cursor gets
reset. Do not reuse an old daemon cursor without handling this case.

Stored-data changes such as `messages`, `conversation`, `tree`, `members`,
`spaces`, `people`, `folders`, `settings` and `status` tell the client what to
read again. Ephemeral changes carry complete current values: `typing`, `presence`,
`occupants`, `searched`, `upload`, `call`, `sign_in`, `playback`, `meter`.
A `media` change carries the updated file descriptor. Empty lists/null values
clear prior ephemeral state; they are not instructions to keep stale values.

## Watch and member lists

Watch replaces the **whole** Watching object. Omitted collections/defaults clear
prior selections; it is not a patch. Watch state is daemon-wide, not owned by its
socket connection: multiple clients are last-writer-wins. Closing the connection
that sent Watch does not itself clear it. The reference expires it after 90
seconds without Wait activity. Wait refreshes that activity timestamp.

`conversation` selects the open conversation; `space` independently names the
visible server/workspace tree. `people` requests relevant presence; `rows` names
visible conversation rows for previews. `members` is `[offset, count]` for the
visible member range, **not** an inclusive `[first, last]` interval.

For Discord, Watch owns the live member subscription. Members reads a cache
snapshot immediately and MUST NOT move that subscription merely because the
client queries a different or uncached page. A pending response is not an empty
roster or a permanent failure:

```json
{"op":"members","conversation":{"network":"discord","account":"1000","id":"4101"},"sections":[],"offset":0,"members":[],"pending":true}
```

On a member-data change, read the wanted page again. TinyClient also performs a
250 ms cache-only fallback poll. A complete response with no members can be valid
beyond the end of the roster; its pending flag is false/omitted. Other adapters
can have different fetching behavior while using the same response model.

## Sending, state transitions and files

An accepted Send returns Sent containing a **pending** Message; it does not wait
for the remote service to acknowledge delivery. The message is stored and change
notifications emitted before the adapter completes the send. `client_id` is a
client-generated correlation ID for this logical message, not a general RPC ID.

```json
{"op":"send","conversation":{"network":"discord","account":"1000","id":"4101"},"client_id":"1730000000000000009","text":"hello"}
```

Later Messages snapshots expose the confirmed message with its service ID and
matching client_id, or a failed state with a reason. A replacement MUST preserve
this correlation and avoid producing duplicate pending/confirmed rows. An
Offline error refuses the send before storing it. A lost IPC response after a
mutation is ambiguous; the protocol does not promise exactly-once execution or
make arbitrary replay of Send safe. Reconcile using snapshots and client_id.

Outgoing files are supplied by local paths in `with.files`; chatd reads/uploads
them. Fetch requests identify **registered media IDs**, not arbitrary URLs. A
Fetch response may return a descriptor whose path is not ready yet; later media
changes expose the available path or failure. A failed fetch is not retried on
every repaint; retry must be requested or its registered source refreshed.

Capabilities and conversation-specific reaction rules constrain mutations.
Unsupported features SHOULD return a structured unsupported/refused error,
rather than claim success without carrying out the requested operation.

## Errors, limits and scheduling

Every request can return `{"op":"error","code":...,"detail":...}`. Codes are
`offline`, `not_found`, `call_active`, `no_call`, `media`, `sign_in`,
`sign_in_unreachable`, `sign_in_blocked`, `unsupported`, `refused`, `too_large`,
`internal`. Detail is display text, not a stable machine-readable identifier.

```json
{"op":"error","code":"offline","detail":"Discord is offline"}
```

Ordinary list responses are capped at 200 rows; Tree supports up to 500. Relevant
additional caps include Watch.people 500, Watch.rows 100, pinned messages 50,
attachments 10 and waveform bars 256. Account capabilities may impose lower
limits. The frame limit still applies to the whole encoded response. There is no
unbounded enumerate-everything operation.

Cache-backed reads should not queue behind HTTP backfill or a long poll. Some
operations legitimately wait for adapter answers, keychain interaction or user
sign-in; clients need separate connections and suitable timeouts. Cancellation
is explicit where modeled (`cancel_send`, `sign_in_cancel`); closing a socket
does not generally cancel a server-side mutation already handed to an adapter.

## Successful response families

The following table maps all operations to their usual successful response.
An error response remains possible. Operation field definitions and the detailed
response structures are in the type catalogue.

| Request operations | Success `op` |
| --- | --- |
| `ping` | `pong` |
| `status`, `read_sessions`, `sign_in`, `sign_out`, `call_start`, `call_accept`, `call_decline`, `call_end`, `call_set`, `media` | `status` |
| `wait` | `changes` |
| `inbox`, `home`, `threads`, `topics`, `in_voice`, `find` | `conversations` |
| `spaces` | `spaces` |
| `tree` | `tree` |
| `conversation`, `start_direct` | `conversation` |
| `collapse`, `star`, `set_draft`, `set_mute`, `leave`, `close_direct`, `relate`, `set_presence`, `mark_read`, `cancel_send`, `discard`, `typing`, `react`, `edit`, `delete`, `sign_in_cancel`, `play`, `set`, `reset_settings`, `shutdown`, `clear`, `test_microphone`, `test_sound` | `ok` |
| `search_messages` | `message_hits` |
| `folders` | `folders` |
| `around` | `around` |
| `people` | `people` |
| `members` | `members` |
| `profile` | `profile` |
| `conversation_info` | `conversation_info` |
| `space_info` | `space_info` |
| `pinned` | `pinned` |
| `shared` | `shared` |
| `watch` | `watching` |
| `messages` | `messages` |
| `send`, `retry` | `sent` |
| `reactions` | `reactions` |
| `catalog` | `catalog` |
| `fetch` | `media` |
| `sign_in_begin`, `sign_in_answer` | `sign_in` |
| `handoff` | `link` |
| `settings` | `settings` |
| `storage` | `storage` |
| `prunable` | `prunable` |

## Implementing a replacement

Implement the local protocol independently of storage and service transports.
The GUI does not require Rust object layouts, the original thread layout, or the
original SQL tables. It does require correct identities, model values, cursor
reset behavior, pending-send correlation and asynchronous change visibility.

A practical compatibility progression is:

1. Isolated profile, process lock, framing, Ping, Status, version/startup behavior.
2. Static fixture conversations, Messages, Watch, Wait, changes and reset recovery.
3. One real service: read state, pending send/echo/failure, media, sign-in and restart.
4. Pagination, bounds, offline/reconnect behavior and responsiveness under load.
5. Other services, settings, capabilities and optional call/playback helpers.

A subset is useful for experimentation, but is not a full drop-in implementation.
Report unsupported features honestly. Preserve or deliberately migrate saved
credentials and Signal cryptographic state before using an existing profile.
Database format compatibility is a separate decision from IPC compatibility.
Do not test a replacement against the live profile while another daemon owns it.

There is currently no published standalone conformance suite or JSON Schema.
The type catalogue is a source-derived reference, not a JSON Schema validator.
Existing Rust integration tests exercise real daemon processes against fake
services, but their launchers use Cargo's compile-time executable path. Running
those tests against another-language daemon requires adapting the launchers;
setting an environment variable alone does not automatically retarget them.

Suggested black-box conformance cases include fragmented frames; malformed JSON;
unknown operations; oversized input/output; multiple requests on one connection;
Wait on a separate connection; missing/default fields; UTF-8 spans; reset after
restart; whole-object/global Watch; pending sends and echo correlation; delayed
media; and a member cache miss during a newer viewport selection. Test intended
behavior separately from the known reference-daemon defects in #42–#44.

## Minimal Linux client

This example performs a read-only Ping against an already running daemon. It
shows byte framing and partial-read handling; it does not implement GUI startup,
reconnection, request retries or the full response model.

```python
import json
import os
import socket
import struct
from pathlib import Path

LIMIT = 1_048_576

def read_exact(stream, count):
    result = bytearray()
    while len(result) < count:
        part = stream.recv(count - len(result))
        if not part:
            raise EOFError("incomplete frame")
        result.extend(part)
    return bytes(result)

def request(stream, value):
    payload = json.dumps(value, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    if len(payload) > LIMIT:
        raise ValueError("request too large")
    stream.sendall(struct.pack(">I", len(payload)) + payload)
    length, = struct.unpack(">I", read_exact(stream, 4))
    if length > LIMIT:
        raise ValueError("response too large")
    return json.loads(read_exact(stream, length))

base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
profile = Path(os.environ.get("TINYCLIENT_DIR", str(base / "tinyclient")))
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
    stream.settimeout(3)
    stream.connect(str(profile / "chat.sock"))
    print(request(stream, {"op": "ping"}))
```

## Reference implementation sources

The pinned sources resolve ambiguities beyond this document. Optionality is
specified by the serialized definitions, not by whether a Rust field happens
to be public or its type implements a programmatic Default trait.

- [Framing, Request, Response, Change and common types](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/lib.rs).
- [Unix socket / Windows pipe mapping](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/ipc.rs).
- [Process discovery and launch](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/launch.rs).
- [Request dispatch and observable operation behavior](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/chatd/src/server.rs).
- [Change coalescing, sequence cursors and Watch ownership](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/chatd/src/hub.rs).
- [Messages, spans and media descriptors](https://github.com/itz4blitz/tinyclient/blob/7b98c4c89129a72cb8f3d4af5ac0bac13b28fa91/crates/protocol/src/message.rs).

The specification and catalogue were checked against these sources, and the
JSON examples were decoded using the reference Rust protocol types. They are a
snapshot specification, not a new negotiated protocol version.
