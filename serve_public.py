"""Serve the generated website bundle on loopback for a public tunnel."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PUBLIC = Path(__file__).resolve().parent / "output" / "public_site"


class WebsiteHandler(SimpleHTTPRequestHandler):
    def list_directory(self, path):
        self.send_error(404, "Not Found")
        return None

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


if __name__ == "__main__":
    if not (PUBLIC / "index.html").is_file():
        raise SystemExit("Run python3 build_public.py first.")
    server = ThreadingHTTPServer(("127.0.0.1", 8766), partial(WebsiteHandler, directory=str(PUBLIC)))
    print("Website bundle available at http://127.0.0.1:8766", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
