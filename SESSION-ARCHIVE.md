# Historical TinyClient session snapshot

This branch preserves the working source, standalone daemon audit, benchmarks,
IPC specification and supporting documentation from 18 October 2026. It is an
archive, not a merge candidate or an updated upstream release.

The category, member-cache and Linux reconnect fixes were merged upstream as
PRs #38, #40 and #45. The documentation is also published separately on
`vbmithr:docs/chatd-ipc-reference`. This snapshot retains the older local base
and applied changes rather than rewriting its history to look like current main.

The audit report and synthetic logs are in `docs/audit-2026-10-18/`.
`docs/testing-chatd.md` describes the tests and two deliberately ignored fault
reproducers. Their failure status describes the audited snapshot, not a claim
about future upstream versions. Build caches are excluded.

The IPC reference tools preserve the temporary generators used for the docs.
From the repository root, with the matching Rust dependencies available:

```sh
cargo run --offline --manifest-path tools/ipc-reference/Cargo.toml \
  --bin chatd-ipc-catalogue-tool -- crates/protocol/src > /tmp/chatd-types.json
python3 tools/ipc-reference/render.py /tmp/chatd-types.json /tmp/chatd-ipc-types.md
cargo run --offline --manifest-path tools/ipc-reference/Cargo.toml --bin validate
```

The catalogue and validator target the documented protocol snapshot. They are
not a general JSON Schema or a conformance test suite for arbitrary future APIs.

AUR recipes, packaging patches, handoff notes and private diagnostic metadata are
preserved separately in a local archive outside the original build directory;
those operational notes are not published on this branch.
