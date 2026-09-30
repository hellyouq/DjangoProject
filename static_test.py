"""Run static_test_harness.js inside a real Chrome against an exported build.

Serves the build on a local port, injects the harness into an exported case page,
drives headless Chrome and reports the PASS/FAIL block the harness prints.
"""

import http.server
import os
import re
import shutil
import socketserver
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
HARNESS = ROOT / "static_test_harness.js"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT = 8914

PAGE = "/case/neon-tokio/"


class Handler(http.server.SimpleHTTPRequestHandler):
    prefix = ""

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(SITE), **kw)

    def translate_path(self, path):
        prefix = Handler.prefix
        if prefix and (path == prefix or path.startswith(prefix + "/")):
            path = path[len(prefix):] or "/"
        return super().translate_path(path)

    def log_message(self, *a):
        pass


def main() -> int:
    if not (SITE / "index.html").exists():
        print("run `manage.py export_site _site` first")
        return 2

    base = sys.argv[1] if len(sys.argv) > 1 else ""
    mount = ("/" + base.strip("/")) if base.strip("/") else ""
    Handler.prefix = mount
    prefix = mount

    js = HARNESS.read_text(encoding="utf-8")
    html = (SITE / "index.html").read_text(encoding="utf-8")
    html = html.replace("</body>", f'<pre id="out">PENDING</pre>\n<script>{js}</script>\n</body>')
    (SITE / "__harness.html").write_text(html, encoding="utf-8")

    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    profile = os.path.join(os.environ["TEMP"], "cr-sakura-test")
    shutil.rmtree(profile, ignore_errors=True)
    proc = subprocess.run(
        [
            CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
            f"--user-data-dir={profile}",
            "--virtual-time-budget=60000",
            "--dump-dom",
            f"http://127.0.0.1:{PORT}{prefix}/__harness.html",
        ],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
    )
    srv.shutdown()
    (SITE / "__harness.html").unlink(missing_ok=True)

    dom = proc.stdout or ""
    m = re.search(r"BEGIN\s*(.*?)\s*END", dom, re.S)
    if not m:
        print("harness produced no result block")
        print("title:", re.search(r"<title>(.*?)</title>", dom, re.S).group(1) if "<title>" in dom else "?")
        return 1
    block = m.group(1)
    print(block)
    failed = [l for l in block.splitlines() if l.startswith("FAIL")]
    print()
    print(f"{len(block.splitlines()) - len(failed)} passed, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
