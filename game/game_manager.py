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

REMATCH = "rematch"


class GameManager:
    def __init__(self, my_id, me, opponent, connection, max_laps, schedule):
        self.my_id = my_id
        self.me = me
        self.opponent = opponent
        self.connection = connection
        self.max_laps = max_laps
        self._schedule = schedule  # schedule(ms, fn): run fn later on the GUI thread
        self.stack = ActionStack(config.MAX_STACK_SIZE)
        self.opponent_left = False
        self.i_want_rematch = False
        self.opponent_wants_rematch = False
        self._inbox = queue.Queue()
        self._generation = 0
        self._reset_race()

    def _reset_race(self):
        self.stack.clear()
        self.resolving = False
        self.winner = None  # becomes "me", "opponent" or "tie"
        self._resolve_at = None

    def schedule(self, ms, fn):
        """Run fn after ms milliseconds, unless a rematch starts first.

        Timed effects (nitro wearing off, a firewall dropping) must not leak
        into the next race, so each one remembers which race it belongs to.
        """
        generation = self._generation

        def guarded():
            if generation == self._generation:
                fn()

        self._schedule(ms, guarded)

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
            elif line == REMATCH:
                self.opponent_wants_rematch = True
            else:
                self._handle_action_line(line)

    def _handle_action_line(self, line):
        try:
            action = Action.decode(line)
        except ValueError:
            print(f"Ignoring unexpected message: {line!r}")
            return
        if action.owner != self.my_id:
            print(f"Opponent cast {BOOSTS[action.boost].name}")
            self._push(action)

    def can_cast(self, index):
        """Whether the local player could cast this boost right now."""
        return (
            not self.resolving
            and not self.winner
            and not self.stack.is_full()
            and self.me.can_afford(BOOSTS[index].cost)
            and not self.opponent.firewall_active
        )

    def cast(self, index):
        """The local player pressed a boost button."""
        boost = BOOSTS[index]
        if not self.can_cast(index):
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

    # Rematch: both players have to ask for one before the race restarts.

    def request_rematch(self):
        if not self.i_want_rematch:
            self.i_want_rematch = True
            self.connection.send(REMATCH)

    def rematch_ready(self):
        return self.i_want_rematch and self.opponent_wants_rematch

    def start_rematch(self):
        self._generation += 1  # cancels every pending timed effect
        self.me.reset()
        self.opponent.reset()
        self._reset_race()
        self.i_want_rematch = False
        self.opponent_wants_rematch = False

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
