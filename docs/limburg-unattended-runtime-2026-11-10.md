# Interrupted and unattended local execution — 10 November 2026

Brian needs to close the Mac repeatedly next week and may leave it computing
while away in approximately two weeks. Azure must absorb inactive outputs before
local space becomes a problem. These are execution requirements for the accepted
mapping study, not additional scientific experiments. **Specification only:** no
new queue, launch agent, cloud resource, notification or deletion was activated.

## What exists and what does not

The existing queue supervises one MPS/two CPU lanes, holds locks, records progress,
uses caffeinate against idle sleep, and has verified result-backup/retirement code.
`scripts/207_preserve_applied_results.py` uploads content-addressed bundles,
reads them back and checks every member. It renews storage access tokens through
Azure CLI; long unattended access is not thereby guaranteed.

`scripts/192_tune_applied_water.py` saves selected best model weights, but not a
complete optimizer/scheduler/RNG training-resume state. Its inference recovery
must not be described as epoch-resumable training. The new scoped runner needs
that integration before it can satisfy the requirements below. Do not reactivate
an old queue merely because its process-supervision code is reusable.

Read-only machine check: FileVault is On. Configured idle sleep is1minute on AC
and battery, although a run-owned power assertion can prevent idle sleep. No
power/security setting was changed. Lid closure normally sleeps the Mac; a
power assertion must not be sold as a guarantee of closed-lid computation.
[Apple sleep settings](https://support.apple.com/en-gb/guide/mac-help/mchle41a6ccd/mac).

## Required behavior

| Situation | Intended response |
| --- | --- |
| Lid closure / ordinary sleep | Computation and upload stop while asleep. Processes may resume normally after wake; allow wake grace and verify worker/device state. Do not count sleep as a training failure or recoverable-stall timeout. |
| Planned close | Offer a cooperative pause: finish the current bounded unit, flush atomic state and publish a planned-pause heartbeat when connected. No command is advertised until implemented. |
| MPS/process failure after wake | Restart the same job from its latest valid full training checkpoint or verified inference chunk. Keep scientific settings fixed. |
| Terminal/Codex window closes | Run-owned detached supervisor/logging must continue independently of this chat or terminal. macOS launch-agent restart is proposed for a logged-in user, not installed yet. |
| Reboot / power loss | Restore durable jobs after startup and user login. FileVault may require a person to unlock the Mac; software monitoring cannot guarantee recovery past that screen. |
| Network/upload interruption | Persist the upload queue and retry with backoff; keep local files until remote content verification. Continue only while reserved disk budget permits. |
| Azure authentication failure | Record and alert; do not delete unverified data. Verify a suitable scoped unattended credential before departure rather than assume an interactive CLI session will last. |
| Disk pressure | Start offloading early, stop admitting unsafe writes, retain the50GiB reserve, and resume producers after capacity is restored. |
| Reproducible code/input/numerical failure | Record diagnostics and notify Brian; keep the affected task unresolved. Continue independent tasks only. Do not silently patch code, alter models or erase the failure. |

Sleep recovery, process death and reboot are distinct tests. No local watchdog
can execute while the Mac is asleep or off. A missing remote heartbeat therefore
means unreachable, not a diagnosed crash.

## Durable computation and scientific identity

- Training checkpoints at complete epoch boundaries must include trainable model
  state, immutable frozen-backbone identity, optimizer, scheduler/scaler where
  used, stopping/best-state history, completed epoch, data/sampler order and all
  applicable RNG states. Use atomic writes and keep two valid generations.
- A planned pause may wait for a boundary. Unplanned interruption may require
  repeating the unfinished epoch; this is preferable to silently restarting the
  whole fit or pretending best inference weights include optimizer state.
- Inference checkpoints are complete tile/window work units with policy, model,
  seed, metadata, masks, output checksums and coverage recorded. Never score or
  advertise a partly written output as complete. Resume the exact remaining census.
- Retries preserve training/inference identities and parameters. No automatic
  change to batch size, resolution, seeds, precision, source pool or label rules.
  Device changes need a separately recorded compatible route, not an invisible
  fallback. Correct resume is tested numerically; bitwise MPS identity is not assumed.
- Bounded transient retry policy: initial delays1/5/15minutes for known network/
  storage transients; at most two same-state worker restarts before escalating.
  Permission, checksum, changed-contract and nonfinite-training errors require
  diagnosis rather than endless blind retry. These are proposed execution defaults.

## Automatic Azure offloading

Use the existing private Limburg storage destination and a dedicated new-run
prefix, not another chapter's paths. Preserve the50GiB local free-space reserve.
Begin archival around80GiB free, with hysteresis back toward90GiB when inactive
verified output is available. These are scheduling defaults, not extra scientific
data caps or an instruction to manufacture90GiB if there is nothing safe to retire.

Admission must account for concurrent producers and the next bounded write,
checkpoint and upload/readback scratch before they start. A simple threshold
checked only after a huge write is insufficient. Work pauses if there is no safe
file to retire or upload cannot keep pace; the reserve takes priority.

Use immutable completed chunks and one bounded uploader. Verify remote contents
by download/readback hash, persist the recovery manifest, then retire only local
copies not leased by any active or dependent task. Checkpoints required for
restart, active inputs and unfinished files stay local. Restore an offloaded
input on demand and verify it before use. No other chapter's data is eligible.
An unavailable upload is never permission to delete an unverified file.

Current full-seed probabilities could exceed the available disk even for this
small study, so offloading is part of execution rather than end-of-run cleanup.
Do not trade away probabilities, support or three seeds for unattended operation.

## Monitoring while Brian is away

Publish a small heartbeat every minute when awake/connected: run and job status,
last actual progress, pause reason, completed/remaining units, disk free,
checkpoint age and upload backlog. Use separate process-liveness and meaningful-
progress clocks. Remote monitoring needs its own cloud-side timer/alert rule;
a Mac-only monitor cannot report a dead Mac. No GPU VM is required for monitoring.

Proposed independent alert conditions: persistent job failure; unexplained missing
heartbeat; prolonged awake-time lack of progress; offload/authentication failure
with growing backlog; disk-induced pause; and completed run. Planned pauses and
wake grace suppress inappropriate repeated alerts. Notify on state change and
recovery, with deduplication, rather than sending every poll. Expected connectivity
loss cannot be distinguished automatically from a crash without further evidence.

Brian selected email alerts to `btgillikin@gmail.com`. This records the intended
recipient; no alert service is active yet. No research email will be sent by the
assistant. An authorized automated self-notification is a separate configuration.
Azure supports email/mobile notification through
[action groups](https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/action-groups);
recipient verification may be required. No service or charge was created here.

Automatic assessment means handling documented failure classes and reporting
others. An AI coding agent is not implicitly running in this chat while Brian is
away; unattended code changes or scientific redesign are not proposed.

## Before unattended operation

Integrate and demonstrate: normal pause/resume; sleep/wake including MPS;
forced worker termination and same-state recovery; network loss and resumed
verified upload; low-space admission/offload; supervisor restart; and real alert
receipt from an independent watcher. Test with bounded engineering fixtures,
not a fresh full science grid. Check storage authentication and login/reboot
limitations before departure. These are operational acceptance checks for the
requested unattended service, not conditions for retaining the chapter.

During vacation the Mac needs power and network, and must remain awake for useful
throughput; an open lid with a locked screen is the straightforward arrangement.
Closing it during the coming week is compatible with an interruption-tolerant run,
not continuous computation. Report both active compute time and elapsed time:
48awake hours at8hours/day occupies about6calendar days, plus transfer/idle time.
The current days-scale compute allowance remains provisional until complete1024px
inference and final-source fitting are profiled. Do not promise vacation completion
based on the small download size or source-fit timings alone.
