"""Crawl the exported build over HTTP and verify every asset reference resolves.

Catches the class of bug where templates point at /static/... but the exporter wrote
the files somewhere else, which only shows up as a silent 404 in the browser.
"""

import re
import subprocess
import sys
import threading
import http.server
import socketserver
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen, Request

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
PORT = 8913


class Handler(http.server.SimpleHTTPRequestHandler):
    """Serves _site at /, optionally behind a subpath so --base builds can be audited.

    `prefix` is exposed on the class because SimpleHTTPRequestHandler.translate_path
    is called per request on the instance, and the audit needs it to strip the mount point.
    """

    prefix = ""

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(SITE), **kw)

    def translate_path(self, path):
        prefix = Handler.prefix
        if prefix and (path == prefix or path.startswith(prefix + "/")):
            path = path[len(prefix) :] or "/"
        return super().translate_path(path)

    def log_message(self, *a):
        pass


def fetch(url):
    try:
        with urlopen(Request(url, headers={"User-Agent": "sakura-audit"}), timeout=20) as r:
            return r.status, r.read()
    except Exception as e:  # noqa: BLE001
        return getattr(e, "code", 0), b""


def main() -> int:
    base_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if not (SITE / "index.html").exists():
        print("run `manage.py export_site _site` first")
        return 2

    # when testing a subpath build, the site lives at /sakura/ inside the served root
    prefix = "/" + base_arg.strip("/") if base_arg.strip("/") else ""
    Handler.prefix = prefix

    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{PORT}{prefix}/" if prefix else f"http://127.0.0.1:{PORT}/"

    seeds = [
        prefix + "/",
        prefix + "/cases/",
        prefix + "/collection/",
        prefix + "/market/",
        prefix + "/hall/",
        prefix + "/profile/",
    ]
    seen = set()
    q = deque(seeds)
    bad_links = []
    assets = set()
    pages = 0

    while q and pages < 200:
        path = q.popleft()
        if path in seen:
            continue
        seen.add(path)
        status, body = fetch(urljoin(base, path.lstrip("/")))
        if status != 200:
            bad_links.append((path, status))
            continue
        pages += 1
        html = body.decode("utf-8", "replace")

        for m in re.finditer(r'(?:href|src)="([^"]+)"', html):
            ref = m.group(1)
            if ref.startswith(("http://", "https://", "data:", "mailto:", "#", "javascript:")):
                continue
            full = urljoin(urljoin(base, path.lstrip("/")), ref)
            p = urlparse(full).path
            if p.endswith("/"):
                p += "index.html"
            if p.startswith(prefix + "/static/"):
                assets.add(p)
            elif p.endswith(".html") or p.endswith("/"):
                q.append(p)

    # every referenced static asset must exist
    missing_assets = []
    for a in sorted(assets):
        st, _ = fetch(urljoin(base, a.lstrip("/")))
        if st != 200:
            missing_assets.append((a, st))

    # data.json is fetched by static-mode.js, not referenced from markup
    referenced_by_js = {prefix + "/data.json"}
    for js in (SITE / "static" / "js").glob("*.js"):
        txt = js.read_text(encoding="utf-8")
        referenced_by_js |= {
            prefix + m
            for m in re.findall(r'["\'](/static/[^"\']+|/data\.json)["\']', txt)
        }
        referenced_by_js |= {
            prefix + m
            for m in re.findall(
                r'["\'](/(?:case|girl|collection|market|hall|profile)/[^"\']*)["\']', txt
            )
        }

    on_disk = {
        prefix + "/" + str(p.relative_to(SITE)).replace("\\", "/")
        for p in (SITE / "static").rglob("*")
        if p.is_file()
    }
    known = referenced_by_js | assets
    unreferenced = sorted(on_disk - known)

    # the art tree is intentionally pre-rendered; only data.json is fetched dynamically
    # spot-check every pre-rendered avatar + banner actually serves
    art_files = sorted(p for p in on_disk if p.startswith(prefix + "/static/art/"))
    art_missing = []
    for a in art_files:
        st, _ = fetch(urljoin(base, a.lstrip("/")))
        if st != 200:
            art_missing.append((a, st))

    srv.shutdown()

    print(f"pages crawled  : {pages}")
    print(f"assets in html : {len(assets)}")
    print(f"art files      : {len(art_files)}")
    print(f"js-referenced  : {len(referenced_by_js)}")
    print()
    if bad_links:
        print("BROKEN INTERNAL LINKS")
        for p, s in bad_links[:40]:
            print(f"  {s}  {p}")
    if missing_assets:
        print("MISSING ASSETS (referenced but not served)")
        for a, s in missing_assets[:40]:
            print(f"  {s}  {a}")
    if art_missing:
        print("UNSERVABLE ART FILES")
        for a, s in art_missing[:40]:
            print(f"  {s}  {a}")
    other_unused = [u for u in unreferenced if not u.startswith(prefix + "/static/art/")]
    if other_unused:
        print("unused non-art files:")
        for u in other_unused[:20]:
            print(f"  {u}")

    ok = not bad_links and not missing_assets and not art_missing
    print()
    print("LINK AUDIT PASSED" if ok else "LINK AUDIT FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
