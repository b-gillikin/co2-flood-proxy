# Presto CPU investigation — 2026-10-18

Scope: engineering diagnosis, not a new model/scientific comparison. The census
retains all pixels, contexts, dates, masks and pooling rules. No production source,
checkpoint, runtime or existing output was changed.

## Cause

A three-second read-only macOS stack sample of the live worker showed substantial
model/attention activity. A separate profile on a fixed real 12-month S2 patch
spent 2.63 of 2.65 seconds in encoder calls; 1.30 seconds was scaled-dot-product
attention, with linear layers and GELU also material. Thus model arithmetic is a
real bottleneck on observed patches. This profile excludes tile loading, receipt
writes and unobserved patches; it is not a whole-census I/O accounting.

Presto encodes every observed pixel, in batches of 128, then averages pixel
representations. The planned census scans 1,498,050 patch sequences. Raw scan
percentage is not a linear remaining-time measure: pixel coverage and sequence
length differ, and absent patches still incur preparation/receipt overhead.

## Executed comparisons

Script 108 prepared a fixed 64×64 real patch from twelve 2018 monthly composites,
then tested the final month and complete twelve-month sequence. All pixels in
the fixture were used. Two repeats per configuration; the first baseline call
was profiled and one-frame cold import overhead must not be used as steady-state
performance. This is a bounded engineering fixture, not the scientific event
sample or a claim about all missingness patterns.

| Configuration | One-frame warm seconds | Twelve-frame warm seconds |
|---|---:|---:|
| Live runtime: torch 2.2.1, batch 128, two threads (first session) | 0.311 | 2.655 |
| Same runtime, batch 128, one thread | 0.364 | 3.846 |
| Same runtime, batch 512, two threads | 0.319 | 3.354 |
| Same runtime, batch 512, one thread | 0.403 | 4.885 |
| Live runtime, batch 128, two threads (later session) | 0.364 | 5.682 |
| Live runtime, batch 128, four threads (later session) | 0.345 | 3.859 |
| Isolated torch 2.9.1, batch 128, two threads | 0.228 | 2.451 |
| Isolated torch 2.9.1, batch 128, four threads | 0.202 | 1.919 |

Larger batches did not help; one thread was slower. Four threads and the newer
runtime are promising. Timings on a shared Mac varied substantially even for
the same baseline. Comparing the new four-thread setting with the first stable
baseline suggests approximately 1.4–1.5× encoding speed; the later baseline would
imply larger gains, but claiming those as sustained throughput is unjustified.
There is no evidence here for an order-of-magnitude speedup or a firm new finish
date. Production has not been switched.

Within the original runtime, tested batch/thread changes yielded exactly equal
pooled vectors on these fixtures. New-runtime four-thread versus original
two-thread relative L2 differences were 6.92e-8 (one frame) and 6.24e-8 (twelve),
with maximum absolute differences 4.77e-7 and 2.38e-7. Both passed rtol 1e-5 /
atol 1e-6; within-configuration repeats were exact. This is numerical consistency
on the fixtures, not universal equivalence under every coverage pattern.

## Isolation and operational checks

- Presto was briefly SIGSTOPed during each benchmark session to avoid directly
  competing with itself; controllers guaranteed SIGCONT in `finally` and recorded
  successful resume. OlmoEarth and the scheduler remained running; Galileo remains
  intentionally deferred.
- Existing TerraMind/torch 2.9.1 runtime could not import Presto's ancillary EE
  dependencies. A separate foundation environment aborted with a duplicate OpenMP
  runtime; no unsafe duplicate-library override was used.
- Instead, torch 2.9.1 was installed **only** under ignored
  `logs/presto-runtime-probe/` (74.5 MB wheel; ~393 MB unpacked), then invoked with
  the original Presto Python/dependencies via a subprocess-specific PYTHONPATH.
  No package was installed into a live worker environment. There were no new
  environmental/model-weight downloads.
- The original extraction, input adapter, encoder and model-loader file hashes
  were checked against the running Presto manifest and remain identical.

## Recommended next action

Keep the current run going while deciding whether a modest gain warrants a
controlled migration. If adopted, create an isolated, pinned production route
for batch 128 / four CPU threads and validate a few additional missingness and
sequence fixtures. Record a separate runtime identity; keep current outputs and
do not silently mix runtime fingerprints. A fresh faster run would redo the
completed fraction; assess net time saved rather than kernel speed alone.

No sampling, reducing pixels, shortening histories, changing precision or
loosening coverage was used to manufacture speed. GPU remains occupied by
OlmoEarth then AnySat. Presto's earlier MPS device error is a separate possible
follow-up when the GPU is available, not a reason to launch another GPU worker
now. Disk Cleanup includes the isolated probe packages once no longer needed.

Evidence: accompanying JSON contains fixture/input hashes, individual timings,
cross-runtime comparison and resume records. Detailed profiles and vectors remain
under `logs/presto-cpu-benchmark/`. `scripts/108_benchmark_presto_cpu.py` reproduces
the fixture and comparisons using the held archive and existing runtimes.
