"""Game rules: casting boosts, the countdown, and resolving the stack.

All of this runs on the GUI thread. The network thread only drops incoming
lines into a queue, which the GUI drains each frame, so game state is never
touched by two threads at once.
"""

import queue
import time

import config
from action_stack import Action, ActionStack
from boosts import BOOSTS, apply_boost


class GameManager:
    def __init__(self, my_id, me, opponent, connection, max_laps, schedule):
        self.my_id = my_id
        self.me = me
        self.opponent = opponent
        self.connection = connection
        self.max_laps = max_laps
        self.schedule = schedule  # schedule(ms, fn): run fn later on the GUI thread
        self.stack = ActionStack(config.MAX_STACK_SIZE)
        self.resolving = False
        self.opponent_left = False
        self.winner = None  # becomes "me", "opponent" or "tie"
        self._resolve_at = None
        self._inbox = queue.Queue()

    # Called from the network thread: only touch the queue here.

    def receive(self, line):
        self._inbox.put(line)

    def peer_disconnected(self):
        self._inbox.put(None)

    # Everything below runs on the GUI thread.

    def process_inbox(self):
        while True:
            try:
                line = self._inbox.get_nowait()
            except queue.Empty:
                return
            if line is None:
                print("Opponent disconnected")
                self.opponent_left = True
                continue
            try:
                action = Action.decode(line)
            except ValueError:
                print(f"Ignoring unexpected message: {line!r}")
                continue
            if action.owner != self.my_id:
                print(f"Opponent cast {BOOSTS[action.boost].name}")
                self._push(action)

    def cast(self, index):
        """The local player pressed a boost button."""
        boost = BOOSTS[index]
        if self.resolving or self.winner:
            return
        if self.stack.is_full():
            print("Stack is full")
            return
        if not self.me.can_afford(boost.cost):
            print("Insufficient RAM")
            return
        if self.opponent.firewall_active:
            print(f"Opponent's firewall blocked your {boost.name}")
            return
        self.me.spend(boost.cost)
        action = Action(self.my_id, index)
        self._push(action)
        self.connection.send(action.encode())

    def seconds_until_resolve(self):
        if self._resolve_at is None or self.resolving:
            return None
        return max(0.0, self._resolve_at - time.monotonic())

    def tick(self):
        """Start resolving once nobody has added to the stack for a while."""
        if self.resolving or not len(self.stack):
            return
        if time.monotonic() >= self._resolve_at:
            self.resolving = True
            self.schedule(config.RESOLVE_STEP_MS, self._resolve_next)

    def record_lap(self, my_laps, opponent_laps):
        if self.winner:
            return
        if my_laps >= self.max_laps and opponent_laps >= self.max_laps:
            self.winner = "tie"
        elif my_laps >= self.max_laps:
            self.winner = "me"
        elif opponent_laps >= self.max_laps:
            self.winner = "opponent"

    def _push(self, action):
        self.stack.push(action)
        # Each new action restarts the countdown, giving the other player
        # time to respond before anything resolves.
        self._resolve_at = time.monotonic() + config.COUNTDOWN_SECONDS

    def _resolve_next(self):
        action = self.stack.pop()
        if action:
            self._apply(action)
        if len(self.stack):
            self.schedule(config.RESOLVE_STEP_MS, self._resolve_next)
        else:
            self.resolving = False
            self._resolve_at = None

    def _apply(self, action):
        boost = BOOSTS[action.boost]
        if action.owner == self.my_id:
            caster, defender = self.me, self.opponent
        else:
            caster, defender = self.opponent, self.me
        if defender.firewall_active:
            print(f"{boost.name} from {caster.name} was blocked by a firewall")
            return
        target = defender if boost.is_hack else caster
        print(f"{caster.name} resolved {boost.name} on {target.name}")
        apply_boost(action.boost, target, self.schedule)
