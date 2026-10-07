"""Per-player state: RAM, speed and active effects."""

import config


class Player:
    def __init__(self, name, colour):
        self.name = name
        self.colour = colour
        self.max_ram = config.MAX_RAM
        self.ram = config.STARTING_RAM
        self.recharge_rate = config.RAM_RECHARGE_RATE
        self.speed_multiplier = 1.0
        # Counters rather than booleans, so two overlapping effects of the
        # same kind don't cancel each other when the first one wears off.
        self._firewalls = 0
        self._freezes = 0

    @property
    def firewall_active(self):
        return self._firewalls > 0

    @property
    def speed(self):
        return 0 if self._freezes else self.speed_multiplier

    def recharge(self):
        self.ram = min(self.max_ram, self.ram + self.recharge_rate)

    def can_afford(self, cost):
        return self.ram >= cost

    def spend(self, cost):
        self.ram -= cost

    def multiply_speed(self, factor):
        self.speed_multiplier *= factor
        print(f"{self.name} speed is now {self.speed_multiplier:.2f}")

    def multiply_recharge_rate(self, factor):
        self.recharge_rate *= factor
        print(f"{self.name} RAM recharge rate is now {self.recharge_rate:.2f}")

    def add_firewall(self):
        self._firewalls += 1
        print(f"{self.name} firewall active")

    def remove_firewall(self):
        self._firewalls -= 1
        if not self.firewall_active:
            print(f"{self.name} firewall down")

    def freeze(self):
        self._freezes += 1
        print(f"{self.name} experiences a system shutdown")

    def unfreeze(self):
        self._freezes -= 1
        if not self._freezes:
            print(f"{self.name}'s system is restored")
