#!/usr/bin/env python3
"""
pad. — the host.

Serves the creation (r1/) over plain HTTP on the LAN, keeps a websocket at /ws, and
tells every connected device what is in front on the Mac. The probe from milestone 0
stays reachable under /spikes/.

    python3 mac/serve.py            port 8080
    python3 mac/serve.py 9000       another port

Binds 0.0.0.0 on purpose: the r1 is another device on the same network and has to
reach this process. There is no authentication in this version (see docs/protocol.md).

Milestone 1: context only. Nothing here executes anything.
"""
import base64
import hashlib
import json
import os
import socket
import struct
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from context import ContextError, make_reader, pump  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
R1_DIR = os.path.join(ROOT, "r1")
SPIKES_DIR = os.path.join(ROOT, "spikes")
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
POLL_SECONDS = 0.25

OP_TEXT, OP_CLOSE, OP_PING, OP_PONG = 0x1, 0x8, 0x9, 0xA


def log(line):
    sys.stdout.write("%s  %s\n" % (time.strftime("%H:%M:%S"), line))
    sys.stdout.flush()


# ---------- websocket framing (RFC 6455, server side, no extensions) ----------

def read_frame(rfile):
    """Return (opcode, payload bytes) for one client frame, or None on EOF."""
    head = rfile.read(2)
    if len(head) < 2:
        return None
    b0, b1 = head
    opcode = b0 & 0x0F
    masked = b1 & 0x80
    length = b1 & 0x7F
    if length == 126:
        length = struct.unpack(">H", rfile.read(2))[0]
    elif length == 127:
        length = struct.unpack(">Q", rfile.read(8))[0]
    mask = rfile.read(4) if masked else None
    data = rfile.read(length)
    if mask:
        data = bytes(c ^ mask[i % 4] for i, c in enumerate(data))
    return opcode, data


def write_frame(wfile, opcode, data=b""):
    """Send one unmasked, unfragmented frame server → client."""
    head = bytes([0x80 | opcode])
    n = len(data)
    if n < 126:
        head += bytes([n])
    elif n < 65536:
        head += bytes([126]) + struct.pack(">H", n)
    else:
        head += bytes([127]) + struct.pack(">Q", n)
    wfile.write(head + data)
    wfile.flush()


# ---------- connected devices and what they are told ----------

class Client:
    def __init__(self, handler):
        self.handler = handler
        self.lock = threading.Lock()  # the poller and the handler both write

    def send(self, message):
        data = json.dumps(message).encode()
        with self.lock:
            write_frame(self.handler.wfile, OP_TEXT, data)


clients = set()
clients_lock = threading.Lock()
state = {"context": None, "status": {"t": "status", "state": "offline", "reason": "starting"}}


def broadcast(message):
    with clients_lock:
        targets = list(clients)
    for client in targets:
        try:
            client.send(message)
        except OSError:
            pass  # its reader loop will notice and drop it


def context_loop():
    """Poll what is in front; tell the devices only when it changes. Main thread:
    the Cocoa run loop has to turn between reads or the answer never changes."""
    read = make_reader()
    while True:
        try:
            context = read()
            status = {"t": "status", "state": "linked"}
        except ContextError as e:
            context = None
            status = {"t": "status", "state": "offline", "reason": str(e)}
        if status != state["status"]:
            state["status"] = status
            broadcast(status)
            log("status %s%s" % (status["state"], (" — " + status["reason"]) if "reason" in status else ""))
        if context is not None and context != state["context"]:
            state["context"] = context
            broadcast(context)
            log("front  %s (%s)" % (context["app"], context["name"]))
        pump(POLL_SECONDS)


# ---------- http + websocket ----------

class Handler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"  # browsers refuse a 101 on HTTP/1.0

    def translate_path(self, path):
        # r1/ is the root; spikes/ is mounted at /spikes/ so the probe stays reachable.
        clean = path.split("?", 1)[0].split("#", 1)[0]
        base, rel = R1_DIR, clean
        if clean == "/spikes" or clean.startswith("/spikes/"):
            base, rel = SPIKES_DIR, clean[len("/spikes"):]
        parts = [p for p in rel.split("/") if p and p not in (".", "..")]
        return os.path.join(base, *parts)

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/ws":
            self.websocket()
        else:
            super().do_GET()

    def end_headers(self):
        # The r1 fetches fresh on every open; make sure nothing in between caches.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def websocket(self):
        key = self.headers.get("Sec-WebSocket-Key")
        if self.headers.get("Upgrade", "").lower() != "websocket" or not key:
            self.send_error(400, "expected a websocket upgrade")
            return
        accept = base64.b64encode(hashlib.sha1((key + WS_GUID).encode()).digest()).decode()
        self.send_response(101, "Switching Protocols")
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept)
        self.end_headers()
        self.close_connection = True

        client = Client(self)
        with clients_lock:
            clients.add(client)
        log("device %s connected" % self.client_address[0])
        try:
            # Tell a new device where things stand. No action ever fires on connect.
            client.send(state["status"])
            if state["context"] is not None:
                client.send(state["context"])
            while True:
                frame = read_frame(self.rfile)
                if frame is None:
                    break
                opcode, data = frame
                if opcode == OP_CLOSE:
                    with client.lock:
                        write_frame(self.wfile, OP_CLOSE, data[:2])
                    break
                if opcode == OP_PING:
                    with client.lock:
                        write_frame(self.wfile, OP_PONG, data)
                elif opcode == OP_TEXT:
                    log("device %s says %s" % (self.client_address[0], data.decode("utf-8", "replace")))
        except (ConnectionError, OSError):
            pass
        finally:
            with clients_lock:
                clients.discard(client)
            log("device %s gone" % self.client_address[0])

    def log_message(self, fmt, *args):
        log("%s  %s" % (self.client_address[0], fmt % args))


# ---------- startup ----------

def lan_ip():
    """The address other devices on the network use to reach this machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.0.2.1", 9))  # documentation range; nothing is actually sent
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    ip = lan_ip() or "<this mac's lan address>"
    base = "http://%s:%d" % (ip, port)
    print("pad. host")
    print("creation  %s/" % base)
    print("probe     %s/spikes/probe.html" % base)
    print("install   %s/spikes/install.html   (open on the mac, scan on the r1)" % base)
    print("socket    ws://%s:%d/ws" % (ip, port))
    print("ctrl-c to stop")
    print()
    # The http server lives on a thread; the context loop owns the main thread
    # because that is where the Cocoa run loop is.
    threading.Thread(target=server.serve_forever, name="http", daemon=True).start()
    try:
        context_loop()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
