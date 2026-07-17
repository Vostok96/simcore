from __future__ import annotations

import json
import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parent
MIRROR = ROOT / "mirror"
MANIFEST = ROOT / "docs" / "capture_manifest.json"
BRAND_ICON = ROOT / "MUFFIN_ICONO.jpg"
HOST = os.environ.get("SIMCORE_CLONE_HOST", "127.0.0.1")
PORT = int(os.environ.get("SIMCORE_CLONE_PORT", "8877"))


def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"pages": {}}


def content_type(path: Path, request_path: str) -> str:
    guessed = mimetypes.guess_type(str(path))[0]
    if guessed:
        return guessed
    lowered = request_path.lower()
    if "/content/" in lowered:
        return "text/css; charset=utf-8"
    if "/bundles/" in lowered or "/scripts/" in lowered:
        return "application/javascript; charset=utf-8"
    if path.suffix.lower() in {".html", ".htm"}:
        return "text/html; charset=utf-8"
    return "application/octet-stream"


def safe_mirror_path(request_path: str) -> Path | None:
    rel = request_path.lstrip("/")
    candidate = (MIRROR / rel).resolve()
    try:
        candidate.relative_to(MIRROR.resolve())
    except ValueError:
        return None
    return candidate


class Handler(BaseHTTPRequestHandler):
    manifest: dict = {}

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} - {fmt % args}")

    def send_bytes(self, body: bytes, status: int, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_bytes(body, status, "application/json; charset=utf-8")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.rstrip("/") == "/SIMCORE_WEB/Login/Index":
            self.serve_page("/SIMCORE_WEB/Home/Index")
            return
        self.stub_response(parsed.path)

    def do_PUT(self) -> None:
        self.stub_response(urlparse(self.path).path)

    def do_DELETE(self) -> None:
        self.stub_response(urlparse(self.path).path)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        request_path = unquote(parsed.path)

        if request_path in {"/", "/SIMCORE_WEB", "/SIMCORE_WEB/"}:
            self.serve_page("/SIMCORE_WEB/Home/Index")
            return

        if request_path.startswith("/SIMCORE_WEB/~/"):
            request_path = request_path.replace("/SIMCORE_WEB/~/", "/SIMCORE_WEB/", 1)

        if request_path == "/MUFFIN_ICONO.jpg":
            self.serve_file(BRAND_ICON, request_path)
            return

        if request_path in self.manifest.get("pages", {}):
            self.serve_page(request_path)
            return

        mirror_file = safe_mirror_path(request_path)
        if mirror_file and mirror_file.exists() and mirror_file.is_file():
            self.serve_file(mirror_file, request_path)
            return

        if request_path.startswith("/SIMCORE_WEB/"):
            self.stub_response(request_path)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Recurso no encontrado")

    def serve_page(self, request_path: str) -> None:
        page_rel = self.manifest.get("pages", {}).get(request_path)
        if not page_rel:
            page_rel = self.manifest.get("pages", {}).get("/SIMCORE_WEB/Home/Index")
        if not page_rel:
            self.send_error(HTTPStatus.NOT_FOUND, "Pagina no capturada")
            return
        page_file = (ROOT / page_rel).resolve()
        self.serve_file(page_file, request_path)

    def serve_file(self, path: Path, request_path: str) -> None:
        try:
            path.relative_to(ROOT.resolve())
        except ValueError:
            self.send_error(HTTPStatus.FORBIDDEN, "Ruta fuera del proyecto")
            return
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Archivo no encontrado")
            return
        self.send_bytes(path.read_bytes(), 200, content_type(path, request_path))

    def stub_response(self, request_path: str) -> None:
        lowered = request_path.lower()
        if "download" in lowered or "documentopdf" in lowered or lowered.endswith(".pdf"):
            self.send_bytes(b"PDF no disponible en modo frontend local.", 200, "text/plain; charset=utf-8")
            return
        if any(word in lowered for word in ["guardar", "registrar", "eliminar", "actualizar"]):
            self.send_json({"success": True, "mensaje": "Modo local: backend ficticio pendiente de implementar."})
            return
        self.send_json({
            "data": [],
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "success": True,
            "mensaje": "Modo local: endpoint stub sin datos reales.",
        })


def main() -> None:
    Handler.manifest = load_manifest()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"SIMCORE WEB clone corriendo en http://{HOST}:{PORT}/SIMCORE_WEB/")
    print(f"Mirror: {MIRROR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Servidor detenido")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

