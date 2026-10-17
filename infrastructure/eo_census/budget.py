"""Conservative per-model cloud admission and elapsed-time budget accounting."""

from datetime import datetime, timezone


def remaining_compute_usd(plan, elapsed_hours=0):
    if min(plan["budget_usd"], plan["azure_hourly_usd"]) <= 0 or elapsed_hours < 0:
        raise ValueError("Invalid budget, rate or elapsed time")
    reserve = plan["noncompute_reserve_usd"]
    spent = plan["compute_spent_usd"] + elapsed_hours * plan["azure_hourly_usd"]
    return max(0.0, plan["budget_usd"] - reserve - spent)


def can_start_model(plan, estimate_hours, elapsed_hours=0):
    if estimate_hours is None or estimate_hours <= 0:
        return False
    # Retain 30 minutes for verified packaging/publication and VM shutdown.
    return (estimate_hours + 0.5) * plan["azure_hourly_usd"] <= remaining_compute_usd(
        plan, elapsed_hours
    )


def deadline_seconds(plan, vm_started_utc):
    start = datetime.fromisoformat(vm_started_utc.replace("Z", "+00:00"))
    if start.tzinfo is None:
        raise ValueError("Aware VM allocation time required")
    elapsed = max(0, (datetime.now(timezone.utc) - start).total_seconds())
    return max(0, remaining_compute_usd(plan, elapsed / 3600) / plan["azure_hourly_usd"] * 3600)


def benchmark_seconds(plan, elapsed_hours=0):
    spent = plan["compute_spent_usd"] + elapsed_hours * plan["azure_hourly_usd"]
    pilot_remaining = max(0, plan["benchmark_ceiling_usd"] - spent)
    return (
        min(pilot_remaining, remaining_compute_usd(plan, elapsed_hours))
        / plan["azure_hourly_usd"]
        * 3600
    )
