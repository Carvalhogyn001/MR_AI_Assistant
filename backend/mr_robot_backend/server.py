"""Local prototype manager. Deliberately refuses LAN binding and cross-origin use."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import hmac
import re
from pathlib import Path
import threading
from urllib.parse import urlsplit, parse_qs

from .providers import ProviderError, validate_prompt

STATIC = Path(__file__).resolve().parents[2] / "manager"


class ManagerServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 8

    def __init__(self, port, gateway):
        self.gateway = gateway
        self._workers = threading.BoundedSemaphore(8)
        super().__init__(("127.0.0.1", port), Handler)

    def process_request(self, request, address):
        if not self._workers.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except BaseException:
            self._workers.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self._workers.release()


class Handler(BaseHTTPRequestHandler):
    server_version = "MRRobot"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(3)

    def log_message(self, *_):
        pass  # No prompt, credential, request path or provider body logging.

    def _send(self, code, data, mime="application/json; charset=utf-8"):
        raw = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=True).encode()
        self.close_connection = True
        self.send_response(code)
        for key, value in {"Content-Type": mime, "Content-Length": str(len(raw)), "Cache-Control": "no-store",
                           "Connection": "close", "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY",
                           "Referrer-Policy": "no-referrer", "Permissions-Policy": "microphone=(), camera=()",
                           "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; "
                           "connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"}.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(raw)

    def _boundary(self):
        port = self.server.server_address[1]
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        origins = {"http://" + host for host in hosts}
        if len(self.headers.get_all("Host", [])) != 1 or self.headers.get("Host") not in hosts:
            raise ProviderError("invalid_host")
        if len(self.headers.get_all("Origin", [])) > 1 or ("Origin" in self.headers and self.headers["Origin"] not in origins):
            raise ProviderError("cross_origin_rejected")

    def _authorized(self, manager_only=False):
        return len(self.headers.get_all("Authorization", [])) == 1 and self.server.gateway.authenticate(
            self.headers.get("Authorization"), manager_only)

    def _body(self):
        if self.headers.get("Transfer-Encoding") or len(self.headers.get_all("Content-Length", [])) != 1:
            raise ProviderError("invalid_body_length")
        length = self.headers["Content-Length"]
        if not length.isascii() or not length.isdigit() or len(length) > 5 or not 1 <= int(length) <= 16384:
            raise ProviderError("invalid_body_length")
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            raise ProviderError("json_required")
        raw = self.rfile.read(int(length))
        if len(raw) != int(length):
            raise ProviderError("incomplete_body")
        try:
            def no_constants(_):
                raise ValueError()
            body = json.loads(raw.decode("utf-8"), parse_constant=no_constants)
            if not isinstance(body, dict):
                raise ValueError()
            return body
        except (ValueError, UnicodeError, RecursionError):
            raise ProviderError("invalid_json") from None

    def do_GET(self):
        self._dispatch(False)

    def do_POST(self):
        self._dispatch(True)

    def _dispatch(self, post):
        try:
            self._boundary()
            static = {"/": ("index.html", "text/html; charset=utf-8"),
                      "/app.js": ("app.js", "application/javascript; charset=utf-8"),
                      "/history.js": ("history.js", "application/javascript; charset=utf-8"),
                      "/robot-scene.js": ("robot-scene.js", "application/javascript; charset=utf-8"),
                      "/vendor/three.module.js": ("vendor/three.module.js", "application/javascript; charset=utf-8"),
                      "/vendor/three.core.js": ("vendor/three.core.js", "application/javascript; charset=utf-8"),
                      "/vendor/OrbitControls.js": ("vendor/OrbitControls.js", "application/javascript; charset=utf-8"),
                      "/vendor/RoundedBoxGeometry.js": ("vendor/RoundedBoxGeometry.js", "application/javascript; charset=utf-8"),
                      "/vendor/Geist.woff2": ("vendor/Geist.woff2", "font/woff2"),
                      "/vendor/GeistMono.woff2": ("vendor/GeistMono.woff2", "font/woff2"),
                      "/style.css": ("style.css", "text/css; charset=utf-8")}
            if not post and self.path in static:
                name, mime = static[self.path]
                return self._send(200, (STATIC / name).read_bytes(), mime)
            if not post and urlsplit(self.path).path == "/api/identity":
                query = parse_qs(urlsplit(self.path).query)
                nonce = query.get("nonce", [""])[0]
                if set(query) != {"nonce"} or len(query["nonce"]) != 1 or not re.fullmatch(r"[a-f0-9]{32}", nonce):
                    raise ProviderError("invalid_identity_challenge")
                proof = hmac.digest(self.server.gateway.manager_token.encode(), nonce.encode(), "sha256").hex()
                return self._send(200, {"proof":proof})
            manager_only = self.path != "/v1/chat"
            if not self._authorized(manager_only):
                return self._send(401, {"error": "unauthorized"})
            gateway = self.server.gateway
            if not post:
                if self.path == "/api/status":
                    return self._send(200, gateway.status())
                if self.path == "/api/device":
                    return self._send(200, gateway.device_status())
                if self.path == "/api/image":
                    return self._send(200, gateway.latest_image or {})
            else:
                body = self._body()
                if self.path == "/v1/chat":
                    return self._send(200, gateway.chat(body))
                if self.path == "/api/settings":
                    return self._send(200, gateway.configure(body))
                if self.path == "/api/device/apply-provider" and set(body) == {"provider"}:
                    return self._send(200, gateway.apply_device_provider(body["provider"]))
                if self.path == "/api/voice/start" and set(body) <= {"mode"}:
                    return self._send(200, gateway.voice.start(body.get("mode", "tap")))
                if self.path == "/api/voice/stop" and not body:
                    gateway.automatic.set_paused(True)
                    return self._send(200, gateway.voice.stop(wait=True))
                if self.path == "/api/voice/resume" and not body:
                    gateway.automatic.set_paused(False)
                    return self._send(200, {"voice_paused": False})
                if self.path == "/api/device/connect" and not set(body) - {"port"}:
                    return self._send(200, gateway.automatic.connect(body.get("port")))
                if self.path == "/api/device/disconnect" and not body:
                    gateway.automatic.disconnect()
                    return self._send(200, {"connected": False})
                if self.path == "/api/device/command" and set(body) <= {"operation", "value"} and "operation" in body:
                    return self._send(200, gateway.usb.command(body["operation"], body.get("value")))
                if self.path == "/api/device/reply" and set(body) == {"text", "provider"}:
                    validate_prompt(body["text"])
                    if body["provider"] not in ("mock", "gemini", "openrouter", "compatible"):
                        raise ProviderError("invalid_provider")
                    return self._send(200, {"device_delivery":gateway.usb.show_reply(body["text"],body["provider"])})
            self._send(404, {"error": "not_found"})
        except ProviderError as error:
            code = str(error)
            status = 403 if code in ("invalid_host", "cross_origin_rejected") else 429 if code in (
                "daily_request_limit", "minute_request_limit", "request_in_progress") else 400
            self._send(status, {"error": code})
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            self.close_connection = True
        except Exception:
            self._send(500, {"error": "internal_error"})
