"""A single TCP link between the two players.

Each message is one line of text ending in a newline. TCP is a byte stream,
so without a delimiter two quick messages can arrive glued together.
"""

import socket
import threading
import time


class PeerConnection:
    def __init__(self, sock):
        self._sock = sock
        self._send_lock = threading.Lock()

    @classmethod
    def host(cls, port, bind_address="0.0.0.0"):
        """Wait for the other player to join on `port`."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((bind_address, port))
        server.listen(1)
        print(f"Waiting for an opponent on port {port}...")
        sock, addr = server.accept()
        server.close()
        print(f"Opponent connected from {addr[0]}:{addr[1]}")
        return cls(sock)

    @classmethod
    def join(cls, host, port, attempts=30):
        """Connect to a hosting player, retrying while they start up."""
        for attempt in range(attempts):
            try:
                sock = socket.create_connection((host, port), timeout=5)
                sock.settimeout(None)
                print(f"Connected to {host}:{port}")
                return cls(sock)
            except OSError as error:
                if attempt == attempts - 1:
                    raise ConnectionError(f"could not reach {host}:{port}: {error}") from error
                time.sleep(1)

    def start_receiving(self, on_message, on_disconnect):
        """Call on_message(line) for each line received, on a background thread."""
        thread = threading.Thread(
            target=self._receive_loop, args=(on_message, on_disconnect), daemon=True
        )
        thread.start()

    def send(self, line):
        with self._send_lock:
            try:
                self._sock.sendall((line + "\n").encode("utf-8"))
            except OSError as error:
                print(f"Error sending {line!r}: {error}")

    def close(self):
        try:
            self._sock.close()
        except OSError:
            pass

    def _receive_loop(self, on_message, on_disconnect):
        buffer = ""
        while True:
            try:
                data = self._sock.recv(1024)
            except OSError:
                data = b""
            if not data:
                on_disconnect()
                return
            buffer += data.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line:
                    on_message(line)
