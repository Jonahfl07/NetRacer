"""The stack of pending boosts. The last one cast resolves first."""

from dataclasses import dataclass

from boosts import BOOSTS


@dataclass(frozen=True)
class Action:
    owner: str   # "host" or "guest": who cast it
    boost: int   # index into BOOSTS

    def encode(self):
        return f"{self.owner}.{self.boost}"

    @classmethod
    def decode(cls, text):
        owner, boost = text.split(".", 1)
        boost = int(boost)
        if not 0 <= boost < len(BOOSTS):
            raise ValueError(f"unknown boost {boost}")
        return cls(owner, boost)


class ActionStack:
    def __init__(self, max_size):
        self.max_size = max_size
        self._items = []

    def __len__(self):
        return len(self._items)

    def is_full(self):
        return len(self._items) >= self.max_size

    def push(self, action):
        self._items.append(action)

    def pop(self):
        return self._items.pop() if self._items else None

    def describe(self, my_id):
        """Human-readable contents, oldest first."""
        parts = []
        for action in self._items:
            who = "You" if action.owner == my_id else "Opponent"
            parts.append(f"{who}: {BOOSTS[action.boost].name}")
        return " ---> ".join(parts)
