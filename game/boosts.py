"""The five boosts and hacks a player can cast, and what each one does."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Boost:
    name: str
    cost: int
    is_hack: bool  # hacks hit the opponent; boosts help the caster


NITRO, FIREWALL, HYPERTHREADING, SYSTEM_SHUTDOWN, SPIKE_DEPLOYMENT = range(5)

BOOSTS = [
    Boost("Nitro", 4, is_hack=False),
    Boost("Firewall", 5, is_hack=False),
    Boost("Hyperthreading", 10, is_hack=False),
    Boost("System Shutdown", 9, is_hack=True),
    Boost("Spike Deployment", 3, is_hack=True),
]


def apply_boost(index, target, schedule):
    """Apply boost `index` to `target` (a Player).

    `schedule(ms, fn)` runs `fn` after `ms` milliseconds on the GUI thread,
    which is how timed effects wear off without sleeping in a thread.
    """
    if index == NITRO:
        target.multiply_speed(1.25)
        schedule(5000, lambda: target.multiply_speed(1 / 1.25))
    elif index == FIREWALL:
        target.add_firewall()
        schedule(10000, target.remove_firewall)
    elif index == HYPERTHREADING:
        target.multiply_recharge_rate(1.5)
    elif index == SYSTEM_SHUTDOWN:
        target.freeze()
        schedule(10000, target.unfreeze)
    elif index == SPIKE_DEPLOYMENT:
        target.multiply_speed(0.9)
    else:
        raise ValueError(f"unknown boost {index}")
