"""
Preview server — serves static HTML previews with zero dependencies.

Routes:
  GET /preview/<slug>  →  docs/preview/<slug>/index.html
  GET /                →  simple index listing all previews

No restart needed: new files are served immediately after build.
Uses only Python stdlib (http.server).

Usage:
  python serve.py                  # default port 8111
  python serve.py --port 9000      # custom port
"""

import os
import sys
import argparse
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote

# Add project root to path so we can import config
sys.path.insert(0, str(Path(__file__).resolve().parent))

log = logging.getLogger("openclaw.serve")


class PreviewHandler(BaseHTTPRequestHandler):
    """Serves preview sites from the docs/ directory (matches GitHub Pages layout)."""

    docs_dir: Path = Path("docs")

    def do_GET(self):
        path = unquote(self.path).rstrip("/")

        # GET / — list all previews
        if path == "" or path == "/":
            self._serve_index()
            return

        # GET /preview/<slug> — serve docs/preview/<slug>/index.html
        if path.startswith("/preview/"):
            slug = path[len("/preview/"):]
            # Sanitize: no path traversal
            slug = slug.replace("..", "").replace("/", "").replace("\\", "")
            if not slug:
                self._send_404()
                return
            file_path = self.docs_dir / "preview" / slug / "index.html"
            if file_path.is_file():
                self._serve_file(file_path)
            else:
                self._send_404()
            return

        self._send_404()

    def _serve_index(self):
        """List all preview slugs as clickable links."""
        preview_root = self.docs_dir / "preview"
        if not preview_root.is_dir():
            self._send_html(200, "<h2>No previews yet.</h2><p>Run: python cli.py build</p>")
            return

        slugs = sorted(
            d.name for d in preview_root.iterdir()
            if d.is_dir() and (d / "index.html").is_file()
        )

        if not slugs:
            self._send_html(200, "<h2>No previews yet.</h2><p>Run: python cli.py build</p>")
            return

        links = "\n".join(
            f'<li><a href="/preview/{s}">{s}</a></li>' for s in slugs
        )
        body = (
            "<h2>OpenClaw Preview Sites</h2>"
            f"<p>{len(slugs)} previews available</p>"
            f"<ul>{links}</ul>"
        )
        self._send_html(200, body)

    def _serve_file(self, file_path: Path):
        try:
            content = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            log.error("Error serving %s: %s", file_path, e)
            self._send_404()

    def _send_404(self):
        self._send_html(404, "<h2>404 — Preview not found</h2>")

    def _send_html(self, code: int, body: str):
        html = (
            "<!DOCTYPE html><html><head>"
            '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">'
            "<style>body{font-family:'Inter',sans-serif;max-width:640px;margin:40px auto;padding:0 20px;color:#333}"
            "a{color:#1565C0} ul{list-style:none;padding:0} li{padding:8px 0;border-bottom:1px solid #eee}</style>"
            f"</head><body>{body}</body></html>"
        )
        content = html.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, fmt, *args):
        """Quieter logging — only errors."""
        if args and isinstance(args[0], str) and args[0].startswith("GET"):
            return  # suppress normal GET logs
        log.info(fmt, *args)


def main():
    parser = argparse.ArgumentParser(description="OpenClaw preview server")
    parser.add_argument("--port", type=int, default=None, help="Port (default: from .env or 8111)")
    parser.add_argument("--dir", type=str, default=None, help="Preview directory (default: from .env or ./previews)")
    args = parser.parse_args()

    # Try to load config, fall back to defaults if dotenv not installed
    port = args.port
    preview_dir = args.dir
    try:
        from openclaw import config
        if port is None:
            port = config.PREVIEW_PORT
        if preview_dir is None:
            preview_dir = config.PREVIEW_DIR
    except ImportError:
        pass
    if port is None:
        port = 8111
    if preview_dir is None:
        preview_dir = str(Path(__file__).resolve().parent / "docs")

    docs_path = Path(preview_dir)
    docs_path.mkdir(parents=True, exist_ok=True)
    PreviewHandler.docs_dir = docs_path

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    server = HTTPServer(("0.0.0.0", port), PreviewHandler)
    print(f"Preview server running at http://localhost:{port}")
    print(f"Serving from: {docs_path.resolve()}")
    print(f"Preview URLs: http://localhost:{port}/preview/<slug>")
    print("Press Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
