# Standalone chatd audit, 2026-10-18

Audited the Discord member viewport, cache, command routing and reconnect paths
in upstream main `44ad327` plus PR #40 (`6fa84d4`). Ran the actual release daemon
against local fake HTTP/WebSocket servers with temporary profiles and synthetic
accounts. No GUI participated. The installed service and real account were not
changed. This is a focused audit, not an exhaustive audit of all chat networks.

## Findings

1. **Confirmed startup ordering defect.** Delay READY by 1.5 seconds; send Watch
   after identify but before guild metadata arrives. The connection completes,
   but the desired member subscription is absent during the following 500 ms.
   `watch` stores `seen` before resolving guild/conversation metadata. READY
   calls `sync_subscription` without recomputing the unresolved Watch; identical
   Watches are ignored. An explicit regression reproducer fails. This provides
   a concrete initial-loading failure path, but does not establish that every
   previously observed live blank pane came from this race.
2. **Confirmed lost viewport on resume (issue #42).** Subscribe to channel A,
   drop the connection, select channel B while offline, and resume the same
   session. No subscription for B arrives within 500 ms after resume. The test
   fails in 2.74 seconds overall. `sent` records enqueue state, reconnect clears
   the outbox, and RESUMED does not reconcile the current desired subscription.
3. **Measured budget starvation under a synthetic burst.** 301 Watch updates
   were submitted in 30.730 ms. Exactly 100 subscription frames reached the
   Gateway; the final viewport did not arrive within another 500 ms. A pending
   cache query still returned in 0.989 ms. The rolling command budget can hold
   unsent snapshots until old commands age out of its 60-second window. We did
   not wait for that expiry in this benchmark. This burst bypasses GUI debounce;
   it demonstrates saturation, not the frequency of saturation in normal use.
4. **HTTP isolation works in the tested case.** A history response held for two
   seconds did not block member cache queries with a 500 ms read deadline or
   navigation to a different channel. A subsequent old-channel query did not
   reclaim the live subscription.
5. **Reconnect backoff remains a separate reviewed risk (issue #41).** Generic
   reconnect delay doubles up to 900 seconds. `Context::pause` waits for stop,
   with no connectivity-restored/resume trigger. This audit did not simulate a
   real OS suspend or a 15-minute DNS outage.

The most useful next changes are to reconcile desired viewport state after
READY and RESUMED, distinguish queued state from delivery, and avoid spending
the entire send budget on transient scroll positions. Faster cache reads alone
cannot repair these state transitions.

## Latency benchmark

Each case includes 300 fresh local socket connections, request/response framing,
JSON decoding and assertion of the response state. Cached requests return 50
members. Missing requests return immediate pending snapshots. Neither emits
additional subscriptions. Values are milliseconds from one isolated run.

| Declared members | Cached p50 | Cached p95 | Cached p99 | Pending p50 | Pending p99 | RSS KiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 0.334 | 0.476 | 0.562 | 0.141 | 0.241 | 18,288 |
| 10,000 | 0.314 | 0.496 | 0.586 | 0.132 | 0.229 | 18,328 |
| 1,000,000 | 0.357 | 0.551 | 0.654 | 0.136 | 0.264 | 18,280 |

Only sparse windows are delivered: these numbers do not measure loading a
million actual member records. The maximum cached response across cases was
1.058 ms. For larger declared rosters, 30 viewport changes reached the latest
subscription in 23.5–23.7 ms but emitted 30 frames. Fixture SYNC-to-cache
visibility was 21.7–21.9 ms, including the test's 20 ms polling interval. These
are local transport measurements, not a Discord latency guarantee or CPU profile.

Host: AMD Ryzen AI 7 350, Linux 7.2.9-zen1-1-zen, Rust 1.98.1, release build.

## Validation and artifacts

- Daemon unit tests: 133 passed.
- Full Discord integration suite: 31 passed in 212.23 s, two then-existing
  manual tests ignored. Includes the new stalled-history/navigation test.
- Two explicit fault reproducers: failed as described above, deliberately
  ignored in the ordinary suite while their production defects remain.
- Both manually invoked benchmarks passed. The burst benchmark asserts budget
  compliance and reports final-viewport delivery; it does not assert recovery.
- After adding delayed-READY fixture support, rebuilt the integration executable
  and ran the startup reproducer, both benchmarks across the audit sequence, and
  rechecked the HTTP-isolation test. The full suite was not repeated for the
  default-zero READY delay or the final ignored burst benchmark addition.
- Source diff whitespace check passed. No production code changed during audit.

The adjacent `.log` files contain the synthetic fixture results. `chatd-audit-tests.patch`
is a separate tests/docs patch based on PR #40, not part of the installed package
or its PKGBUILD. Source edits remain in the warmed AUR checkout; an isolated copy
is at `/tmp/tinyclient-chatd-audit`. At audit completion these additions were not yet committed or published. They
are now preserved on the historical session archive branch.
Repeatable test commands are in `src/tinyclient/docs/testing-chatd.md`.

For this run the release mediad binary already existed. The compiled integration
executable was invoked with `CARGO=/usr/bin/true` to bypass its unconditional
mediad debug-build helper; real daemon/fixture execution and assertions were not
bypassed. Build logs and temporary test outputs were under `/tmp` before being
copied to the results directory.
