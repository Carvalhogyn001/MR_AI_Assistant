#!/usr/bin/env python3
"""Run the local manager; --open unlocks its browser without printing a token."""
import argparse
import os
from pathlib import Path
import signal
import sys
import webbrowser
import hmac
import secrets
import json
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import URLError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
from mr_robot_backend.gateway import Gateway
from mr_robot_backend.server import ManagerServer
from mr_robot_backend.providers import NoRedirects, ProviderError


def existing_manager(url, token):
    """Prove the other listener holds our local key before sending it a browser unlock."""
    nonce=secrets.token_hex(16)
    try:
        opener=build_opener(ProxyHandler({}),NoRedirects())
        with opener.open(Request(url+"api/identity?nonce="+nonce),timeout=2) as response:
            raw=response.read(1025)
        if len(raw)>1024:return False
        proof=json.loads(raw).get("proof","")
        expected=hmac.digest(token.encode(),nonce.encode(),"sha256").hex()
        return isinstance(proof,str) and proof.isascii() and hmac.compare_digest(proof,expected)
    except (OSError,URLError,ValueError,AttributeError,RecursionError,ProviderError):
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=18765)
    parser.add_argument("--open", action="store_true", help="Open and unlock the browser; no token appears in logs")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Port must be between 1024 and 65535")
    os.umask(0o077)
    gateway = Gateway(ROOT / "private/host")
    url = f"http://127.0.0.1:{args.port}/"
    try:
        server = ManagerServer(args.port, gateway)
    except OSError:
        if args.open and existing_manager(url,gateway.manager_token):
            webbrowser.open(url+"#access="+gateway.manager_token)
            print("Opened the existing local MR. Robot manager; no second server started.")
            return
        parser.exit(1, "Local port unavailable. Choose another --port.\n")
    print(f"MR. Robot manager: {url} (loopback only)", flush=True)
    if args.open:
        # Browser JS consumes then removes the fragment. Provider keys never enter this URL.
        webbrowser.open(url + "#access=" + gateway.manager_token)
    def stop(*_):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, stop)
    gateway.automatic.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        gateway.automatic.close()
        gateway.voice.stop(wait=True)
        gateway.images.close()
        gateway.usb.close()
        server.server_close()


if __name__ == "__main__":
    main()
