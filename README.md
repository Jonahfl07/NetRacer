# Hack Racer

A two-player networked racing game in Python. Each player's car laps a track automatically. You win by spending RAM on boosts and hacks at the right moment. Casts go onto a shared **stack** (like Magic: The Gathering). Every new cast restarts a 5-second countdown so the other player can respond. When the countdown runs out, the stack resolves last-in, first-out.

The window follows the design in my project report ([docs/NetRacer_Report.docx](docs/NetRacer_Report.docx)): a RAM bar along the top, the action stack under it (the next action to resolve is on the left, blue is yours and orange is your opponent's), boosts down the left in green, hacks down the right in red, and the track in the middle.

I first wrote this at 16 to learn sockets, threading and GUI programming. I later restructured it into modules and fixed the bugs listed under [What changed in the cleanup](#what-changed-in-the-cleanup).

## Running it

Requires Python 3.9+ with Tkinter.

**On a Mac:** double-click `NetRacer.app` (the first time, right-click it, choose Open, then Open again). It asks whether to play on this Mac, host, or join a friend, and shows a how-to-play page describing each boost and hack before the game starts. It needs `pip install -r requirements.txt` to have been run once.

Or from a terminal:

```bash
pip install -r requirements.txt

# Terminal / machine 1: the host, waits on port 5000
python main.py

# Terminal / machine 2: joins the host
python main1.py                     # same machine
python main1.py 192.168.1.20        # another machine on your network (HOST or HOST:PORT)
```

Before each race the two players vote on how many laps it should be (3, 5, 10, 15 or 20). Both votes are revealed and one is picked at random. Options (both scripts): `--laps N` skips the vote and races N laps (use the same value on both sides), and `--car` / `--opponent-car` to use your own car images instead of the default circles. The host also takes `--port`. When a race ends, the game window switches to a result screen, and either player can click **Rematch**, and the race restarts once both have.

## Boosts and hacks

| Name | RAM | Effect |
|---|---|---|
| Nitro | 4 | Your speed x1.25 for 5 s |
| Firewall | 5 | For 10 s, your opponent can't cast hacks against you, and their hacks resolving on the stack are cancelled. Boosts are unaffected |
| Hyperthreading | 10 | Your RAM recharge rate x1.5 for the rest of the race |
| System Shutdown | 9 | *Hack:* freezes your opponent for 10 s |
| Spike Deployment | 3 | *Hack:* your opponent's speed x0.9 for the rest of the race |

RAM recharges at 0.2 per second, up to a maximum of 12. The stack holds up to 6 actions.

## How it works

| File | Responsibility |
|---|---|
| `main.py`, `main1.py` | Launchers: `main.py` hosts, `main1.py` joins |
| `game/cli.py` | Command-line arguments, wiring everything together |
| `game/network.py` | One TCP connection between the players, with newline-delimited messages |
| `game/game_manager.py` | Rules: casting, the countdown, resolving the stack, win detection |
| `game/action_stack.py` | The stack and the wire format for an action (`host.3` = host cast boost 3) |
| `game/boosts.py` | Boost definitions and their effects |
| `game/player.py` | RAM, speed, firewall and freeze state |
| `game/car.py` | Car movement and lap counting |
| `game/gui.py` | The guizero window: RAM bar, stack row, buttons, track and the end-of-race screen |

**Threading model.** Only the network reader runs on a background thread, and all it does is put incoming lines on a `queue.Queue`. The GUI thread drains that queue every frame, so all game state is changed from a single thread. Timed effects (nitro, firewall, shutdown) are scheduled with Tk's `after()` instead of `time.sleep()` in worker threads, so the code needs no locks.

**Peer to peer.** There is no server deciding what happens. Both clients receive the same casts and resolve the stack locally with the same rules, and each simulates both cars.

## Known limitations

- The two clients aren't clock-synchronised, so lap timings can drift slightly between screens over a long race.
- Car speed is tied to frame rate, so a slow machine has slow cars on its screen.
- Nothing is encrypted or authenticated. Only play on a network you trust.

## What changed in the cleanup

- **A networking bug.** The server side only handled boosts nested inside an `if message == "ready"` check, so the hosting player ignored every boost the other player cast.
- **Message framing.** Messages are now newline-delimited. Previously, two quick casts could arrive glued together in one `recv()` and crash the parser.
- **Thread safety.** Game logic and GUI updates used to run from several threads at once, and Tkinter isn't thread-safe. Now only the network reader is threaded.
- **Globals.** Classes no longer depend on module-level variables like `port`, `my_boosts` and `opponent_boosts`.
- **Overlapping effects.** A second firewall or nitro used to cancel or overwrite the first, and System Shutdown reset speed to 1, wiping any slowdowns. Effects now stack and undo themselves cleanly.
- **Lap counting.** Laps are counted when a car turns the final corner. Previously, a car frozen on the start line gained a lap every frame.
- **The "you lost" screen** crashed. It now works, and a tie is handled too.
- **RAM costs.** RAM is now charged when you cast. Previously, only the top item of the stack was charged.
- **Hardcoded paths and ports** were replaced with command-line options, and the cars are now drawn in code, so the game needs no image files.
- **GUI redesign** to match the report: RAM bar, stack row with colour-coded entries, green boost and red hack buttons that grey out when you can't use them, and a result screen with Rematch and Quit.
- Removed duplicate imports and dead code (`update_speed`, `check_boundaries`).
