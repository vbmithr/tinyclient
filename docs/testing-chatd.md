# Testing chatd without the GUI

The Discord integration fixture starts the real `chatd` binary in a temporary
profile with fake HTTP and Gateway servers on loopback. It uses synthetic tokens
and member data. It does not connect to Discord or use the desktop's profile.

Build both daemons and the integration executable in the same profile:

```sh
cargo build --frozen --release -p chatd -p mediad
cargo test --frozen --release -p chatd --test discord --no-run
cargo test --frozen --release -p chatd --lib
cargo test --frozen --release -p chatd --test discord
```

Run the latency benchmark separately from other tests:

```sh
cargo test --frozen --release -p chatd --test discord \
  bench_member_viewport_without_gui -- \
  --exact --ignored --nocapture --test-threads=1
```

The benchmark reports p50/p95/p99/max IPC latency over 300 reads per case,
including a fresh local socket connection and response decoding on every read.
It checks both cached 50-member pages and immediate pending snapshots. Declared
roster sizes are 100, 10,000 and 1,000,000; only requested windows are delivered,
so this measures sparse window access, not enumerating those entire rosters.
Cache queries must not emit Gateway subscriptions. Larger cases also report the
time to deliver the latest of 30 viewport changes, fixture SYNC-to-cache latency,
and daemon RSS. Fixture timing includes its polling and the test's 20 ms probes;
it is not a measurement of Discord's network latency. No timing percentiles are
CI pass/fail thresholds.

`member_cache_reads_and_navigation_continue_during_stalled_history` holds a
history HTTP response for two seconds. Member reads have a 500 ms socket deadline;
changing channel must still update the subscription, and a query for the old
channel must not reclaim it.

The existing dropped-socket test covers successful session resume, presence,
messages, heartbeats and token expiry. It does not cover lost queued viewport
changes. The explicit reproducer for issue #42 is ignored in the normal suite
because it currently fails:

```sh
cargo test --frozen --release -p chatd --test discord \
  member_viewport_changed_while_offline_is_delivered_after_resume -- \
  --exact --ignored --nocapture
```

Remove that ignore when the recovery bug is fixed. A passing ordinary suite does
not establish recovery from an outage long enough to reach reconnect backoff,
real laptop suspend, a blackholed socket, or an unanswered initial member SYNC.
Those require additional controlled fault injection or live diagnostics.

A second ignored reproducer delays the Gateway's initial `READY` by 1.5 seconds
and selects the member viewport after identify but before guild metadata exists:

```sh
cargo test --frozen --release -p chatd --test discord \
  member_viewport_selected_before_ready_is_subscribed_after_connect -- \
  --exact --ignored --nocapture
```

It currently fails: the desired channel is not subscribed within 500 ms after
connection completes. The Watch was recorded before it could be resolved against
guild metadata; READY does not force that Watch to be evaluated again. This is a
controlled reproduction of a startup ordering defect, not proof that every live
blank pane has this cause.

For sustained subscription pressure, run this separate stress benchmark:

```sh
cargo test --frozen --release -p chatd --test discord \
  bench_member_subscription_burst_without_gui -- \
  --exact --ignored --nocapture --test-threads=1
```

It submits 300 changes over plausible member offsets and one final distinct
viewport, then reports whether that final viewport reaches the fake Gateway
within 500 ms. It also measures a pending cache read and verifies the configured
100-command budget is respected. A quick IPC reply does not imply that the
latest subscription has been delivered. This is deliberately more aggressive
than the GUI's viewport debounce and does not model typical human scrolling.
