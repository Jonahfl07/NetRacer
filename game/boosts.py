"""The five boosts and hacks a player can cast, and what each one does."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Boost:
    name: str
    cost: int
    is_hack: bool  # hacks hit the opponent; boosts help the caster
    description: str = ""  # shown on the how-to-play page


NITRO, FIREWALL, HYPERTHREADING, SYSTEM_SHUTDOWN, SPIKE_DEPLOYMENT = range(5)

BOOSTS = [
    Boost("Nitro", 4, is_hack=False,
          description="Your car is 25% faster for 5 seconds."),
    Boost("Firewall", 5, is_hack=False,
          description="For 10 seconds your opponent can't hack you, and their hacks on the stack are cancelled."),
    Boost("Hyperthreading", 10, is_hack=False,
          description="Your RAM recharges 1.5x faster for the rest of the race."),
    Boost("System Shutdown", 9, is_hack=True,
          description="Freezes your opponent's car for 10 seconds."),
    Boost("Spike Deployment", 3, is_hack=True,
          description="Your opponent's car is 10% slower for the rest of the race."),
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
