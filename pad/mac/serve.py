#!/usr/bin/env python3
"""
pad. — milestone 0 host.

Serves a folder over plain HTTP on the LAN and answers a websocket upgrade at /ws,
so every line of spikes/probe.html can go green. Standard library only: nothing to
install for the spike. The websocket code here is the seed of the real host; the
HTTP part will be replaced when there is something to serve beyond a probe.

    python3 mac/serve.py            serves ../spikes on port 8080
    python3 mac/serve.py r1         serves ../r1 instead
    python3 mac/serve.py r1 9000    on another port

Binds 0.0.0.0 on purpose: the r1 is another device on the same network and has to
reach this process. There is no authentication in this version (see docs/protocol.md).
"""
import base64
import hashlib
import os
import socket
import struct
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

OP_TEXT, OP_CLOSE, OP_PING, OP_PONG = 0x1, 0x8, 0x9, 0xA


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


class Handler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"  # browsers refuse a 101 on HTTP/1.0

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
        self.log_message("websocket open")
        try:
            while True:
                frame = read_frame(self.rfile)
                if frame is None:
                    break
                opcode, data = frame
                if opcode == OP_CLOSE:
                    write_frame(self.wfile, OP_CLOSE, data[:2])  # echo the code back
                    break
                if opcode == OP_PING:
                    write_frame(self.wfile, OP_PONG, data)
                elif opcode == OP_TEXT:
                    self.log_message("websocket text: %s", data.decode("utf-8", "replace"))
        except (ConnectionError, OSError):
            pass
        self.log_message("websocket closed")

    def log_message(self, fmt, *args):
        sys.stdout.write("%s  %s\n" % (self.client_address[0], fmt % args))
        sys.stdout.flush()


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
    folder = sys.argv[1] if len(sys.argv) > 1 else "spikes"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
    directory = os.path.join(ROOT, folder)
    if not os.path.isdir(directory):
        sys.exit("no such folder to serve: %s" % directory)

    def handler(*a, **kw):
        return Handler(*a, directory=directory, **kw)

    server = ThreadingHTTPServer(("0.0.0.0", port), handler)
    ip = lan_ip() or "<this mac's lan address>"
    base = "http://%s:%d" % (ip, port)
    print("pad. host — milestone 0")
    print("serving   %s" % directory)
    print("page      %s/" % base)
    print("install   %s/install.html   (open on the mac, scan on the r1)" % base)
    print("socket    ws://%s:%d/ws" % (ip, port))
    print("ctrl-c to stop")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
