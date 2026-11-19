"""Pure-function burn-rate evaluator (no network, no secrets). See burn_rate_rules.yaml for the policy."""
from dataclasses import dataclass

SLO_PERIOD_HOURS = 720.0


def burn_rate(errors: float, total: float, slo_target: float) -> float:
    """error_ratio / error_budget. total==0 -> 0.0 (no traffic is not an error; the dead-man's switch covers silence)."""
    if not 0.0 < slo_target < 1.0:
        raise ValueError("slo_target must be in (0,1)")
    if total < 0 or errors < 0 or errors > total:
        raise ValueError("need 0 <= errors <= total")
    if total == 0:
        return 0.0
    return (errors / total) / (1.0 - slo_target)


def budget_consumed_pct(burn: float, window_hours: float) -> float:
    return burn * window_hours / SLO_PERIOD_HOURS * 100.0


@dataclass(frozen=True)
class Tier:
    name: str
    severity: str
    long_h: float
    short_h: float
    burn: float


TIERS = (
    Tier("page-fast", "page", 1.0, 5 / 60, 14.4),
    Tier("page-slow", "page", 6.0, 0.5, 6.0),
    Tier("ticket", "ticket", 72.0, 6.0, 1.0),
)


def evaluate(windows: dict, slo_target: float, min_requests: int = 20):
    """windows: {hours: (errors, total)} for every long/short window hours used by TIERS.
    Returns list of firing tier names. A tier fires only if BOTH windows are over threshold
    and the long window has >= min_requests (low-traffic rule)."""
    firing = []
    for t in TIERS:
        le, lt = windows[t.long_h]
        se, st = windows[t.short_h]
        if lt < min_requests:
            continue
        if burn_rate(le, lt, slo_target) >= t.burn and burn_rate(se, st, slo_target) >= t.burn:
            firing.append(t.name)
    return firing
