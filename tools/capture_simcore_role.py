from __future__ import annotations

import json
import os
import re
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

import requests


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_ROOT = ROOT / "role_captures"

BASE_URL = os.environ.get("SIMCORE_SOURCE_URL", "http://192.168.0.220/SIMCORE_WEB/")
ROLE = os.environ.get("SIMCORE_CAPTURE_ROLE", "role").strip() or "role"
USER = os.environ.get("SIMCORE_SOURCE_USER", "")
PASSWORD = os.environ.get("SIMCORE_SOURCE_PASS", "")

HEADERS = {"User-Agent": "Mozilla/5.0"}
SOURCE_NETLOC = urlparse(BASE_URL).netloc
SOURCE_PREFIX = urlparse(BASE_URL).path.rstrip("/") + "/"

SEED_PAGES = [
    "Login/Index",
    "Home/Index",
    "Mic_persona/",
    "Mic_procedencia/",
    "Mic_servicio/",
    "Mic_medico/",
    "Mic_res_comentarios_def/",
    "Mic_area/",
    "Mic_examen/",
    "Mic_muestra/",
    "Mic_muestra_contenedor/",
    "Mic_parametro/",
    "mic_orga_panel/",
    "Mic_res_panel_recuento/",
    "Mic_orga/",
    "Mic_antibiotico/",
    "Mic_usuario/",
    "Mic_destinos/",
    "Mic_seccion/",
    "Mic_configuracion_general/",
    "Mic_orden/",
    "Mic_destinos_orden_detalle/",
    "Mic_orden_detalle/Resultado_microbiologia",
    "Trans_consultas/Microbiologia_pac_orden",
    "Trans_consultas/Microbiologia_proce_servi_medico",
    "Trans_reportes/Microbiologia_rep_produccion",
    "Trans_reportes/Microbiologia_rep_idt_ast",
    "Trans_reportes/Microbiologia_rep_botellas",
    "Trans_reportes/Microbiologia_rep_etiquetas_gen",
    "Trans_reportes/Microbiologia_rep_hoja_trabajo",
]

BACKEND_KEYWORDS = {
    "obtener",
    "guardar",
    "eliminar",
    "actualizar",
    "registrar",
    "buscar",
    "listar",
    "validar",
    "exportar",
    "download",
    "documentopdf",
    "pdf",
    "excel",
    "imprimir",
}

ASSET_EXTENSIONS = {
    ".css",
    ".js",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".map",
}


def role_dir() -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", ROLE).strip("_") or "role"
    return CAPTURE_ROOT / safe


def clean_route(route: str) -> str:
    route = route.strip()
    if route.startswith("~/"):
        route = route[2:]
    return route.lstrip("/")


def safe_name(path: str) -> str:
    path = path.strip("/")
    if not path:
        return "index"
    path = path.replace("/", "__")
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", path)


def same_simcore(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.netloc and parsed.netloc != SOURCE_NETLOC:
        return False
    return parsed.path.startswith(SOURCE_PREFIX)


def normalize_url(value: str, current_url: str) -> str | None:
    value = (value or "").strip()
    if not value:
        return None
    if value.startswith("#") or value.lower().startswith(("javascript:", "mailto:", "tel:")):
        return None
    if value.startswith("~/"):
        value = SOURCE_PREFIX + value[2:]
    normalized = urljoin(current_url, value)
    normalized, _frag = urldefrag(normalized)
    if not same_simcore(normalized):
        return None
    return normalized


def route_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.path


def page_path(capture: Path, request_path: str) -> Path:
    return capture / "mirror" / "_pages" / f"{safe_name(request_path)}.html"


def local_asset_path(capture: Path, url: str) -> Path:
    parsed = urlparse(url)
    rel = parsed.path.lstrip("/")
    return capture / "mirror" / rel


def find_values(html: str, attr: str) -> set[str]:
    values: set[str] = set()
    for match in re.findall(attr + r"\s*=\s*([\"'])(.*?)\1", html, flags=re.I | re.S):
        values.add(match[1])
    return values


def find_assets(html: str) -> set[str]:
    values: set[str] = set()
    for tag_attr in ["src", "href", "data-src"]:
        values.update(find_values(html, tag_attr))
    return {v for v in values if looks_like_asset(v)}


def find_page_links(html: str) -> set[str]:
    links: set[str] = set()
    for raw in re.findall(r"<a\b[^>]*>", html, flags=re.I | re.S):
        href_match = re.search(r"href\s*=\s*([\"'])(.*?)\1", raw, flags=re.I | re.S)
        if href_match:
            links.add(href_match.group(2))
    return links


def find_forms(html: str, current_url: str) -> list[dict[str, str]]:
    forms: list[dict[str, str]] = []
    for raw in re.findall(r"<form\b[^>]*>", html, flags=re.I | re.S):
        action = ""
        method = "GET"
        action_match = re.search(r"action\s*=\s*([\"'])(.*?)\1", raw, flags=re.I | re.S)
        method_match = re.search(r"method\s*=\s*([\"'])(.*?)\1", raw, flags=re.I | re.S)
        if action_match:
            action = action_match.group(2)
        if method_match:
            method = method_match.group(2).upper()
        normalized = normalize_url(action or current_url, current_url)
        if normalized:
            forms.append({"method": method, "action": route_from_url(normalized)})
    return forms


def find_css_urls(text: str) -> set[str]:
    found: set[str] = set()
    for raw in re.findall(r"url\(([^)]+)\)", text, flags=re.I):
        raw = raw.strip().strip("'\"")
        if raw and not raw.startswith("data:"):
            found.add(raw)
    return found


def looks_like_asset(value: str) -> bool:
    parsed = urlparse(value)
    lowered = parsed.path.lower()
    if "/content/" in lowered or "/scripts/" in lowered or "/bundles/" in lowered:
        return True
    return Path(lowered).suffix in ASSET_EXTENSIONS


def is_asset_path(path: str) -> bool:
    lowered = path.lower()
    if any(part in lowered for part in ["/content/", "/scripts/", "/bundles/", "/imagenes/", "/webfonts/", "/images/"]):
        return True
    return Path(lowered).suffix in ASSET_EXTENSIONS


def looks_like_backend(path: str) -> bool:
    lowered = path.lower()
    return any(keyword in lowered for keyword in BACKEND_KEYWORDS)


def should_try_as_page(url: str) -> bool:
    parsed = urlparse(url)
    lowered = parsed.path.lower()
    if not same_simcore(url):
        return False
    if Path(lowered).suffix in ASSET_EXTENSIONS:
        return False
    if looks_like_backend(parsed.path):
        return False
    return True


def sanitize_text(text: str) -> str:
    text = re.sub(
        r"(id\s*=\s*['\"]session_user_id['\"][^>]*value\s*=\s*['\"])([^'\"]+)(['\"])",
        r"\1local_demo\3",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"(value\s*=\s*['\"])(admin|[0-9]{8})(['\"][^>]*id\s*=\s*['\"]session_user_id['\"])",
        r"\1local_demo\3",
        text,
        flags=re.I,
    )
    return re.sub(r"\b\d{8}\b", "ID_SANITIZADO", text)


def write_bytes(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def decode_response(response: requests.Response) -> str:
    encoding = response.encoding or "utf-8"
    return response.content.decode(encoding, errors="replace")


def find_backend_endpoints(text: str, current_url: str) -> set[str]:
    endpoints: set[str] = set()
    patterns = [
        r"(?:url|URL)\s*:\s*['\"]([^'\"]+)['\"]",
        r"['\"](/SIMCORE_WEB/[^'\"]+)['\"]",
        r"['\"](~?/[^'\"]*(?:Obtener|Guardar|Eliminar|Actualizar|Registrar|Buscar|Listar|Validar|Exportar|Download|DocumentoPDF|PDF|Excel|Imprimir)[^'\"]*)['\"]",
        r"['\"]([A-Za-z0-9_]+/[A-Za-z0-9_]*(?:Obtener|Guardar|Eliminar|Actualizar|Registrar|Buscar|Listar|Validar|Exportar|Download|DocumentoPDF|PDF|Excel|Imprimir)[^'\"]*)['\"]",
    ]
    for pattern in patterns:
        for value in re.findall(pattern, text, flags=re.I):
            normalized = normalize_url(value, current_url)
            if normalized:
                path = route_from_url(normalized)
                if looks_like_backend(path) and not is_asset_path(path):
                    endpoints.add(path)
    return endpoints


def fetch_asset(
    session: requests.Session,
    capture: Path,
    asset_url: str,
    fetched: set[str],
) -> dict[str, object] | None:
    parsed = urlparse(asset_url)
    key = parsed._replace(query="").geturl()
    if key in fetched:
        return None
    fetched.add(key)
    if not same_simcore(asset_url):
        return None

    try:
        response = session.get(asset_url, headers=HEADERS, timeout=30)
    except requests.RequestException as exc:
        return {"url": asset_url, "status": "ERROR", "error": str(exc)}

    item: dict[str, object] = {
        "url": asset_url,
        "path": route_from_url(asset_url),
        "status": response.status_code,
        "content_type": response.headers.get("content-type", ""),
        "bytes": len(response.content) if response.status_code < 400 else 0,
    }
    if response.status_code >= 400:
        return item

    path = local_asset_path(capture, asset_url)
    body = response.content
    if "/Scripts/Views/" in parsed.path and "javascript" in item["content_type"]:
        body = sanitize_text(decode_response(response)).encode("utf-8")
    write_bytes(path, body)
    item["local_file"] = str(path.relative_to(capture)).replace("\\", "/")
    return item


def build_architecture_md(
    capture: Path,
    role_label: str,
    page_report: list[dict[str, object]],
    endpoint_report: list[dict[str, object]],
    asset_report: list[dict[str, object]],
    forms: list[dict[str, str]],
) -> None:
    controllers = Counter()
    for endpoint in endpoint_report:
        path = str(endpoint.get("path", ""))
        parts = path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "SIMCORE_WEB":
            controllers[parts[1]] += 1

    visible_pages = [p for p in page_report if p.get("stored")]
    errors = [p for p in page_report if not p.get("stored")]
    asset_errors = [a for a in asset_report if a.get("status") != 200]

    lines = [
        f"# Arquitectura capturada - {role_label}",
        "",
        f"Capturado: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Alcance",
        "",
        "Esta carpeta es una captura del SIMCORE visible para este perfil. Incluye HTML renderizado, CSS, JS, imagenes y un inventario de endpoints detectados.",
        "",
        "No incluye el codigo fuente real del backend ASP.NET/C#/MVC porque el servidor no lo entrega por HTTP. Tampoco incluye respuestas de listados, ordenes, resultados ni datos de pacientes.",
        "",
        "## Estructura de carpeta",
        "",
        "```text",
        "mirror/_pages/                         HTML renderizado de pantallas",
        "mirror/SIMCORE_WEB/Content/           CSS y bundles de estilos",
        "mirror/SIMCORE_WEB/Scripts/Views/     JS propio de cada vista",
        "mirror/SIMCORE_WEB/bundles/           jQuery, Bootstrap, Modernizr",
        "mirror/SIMCORE_WEB/Imagenes/          Logo/assets entregados",
        "docs/routes.json                      Paginas probadas y estado HTTP",
        "docs/assets.json                      Recursos descargados o faltantes",
        "docs/endpoints.json                   Endpoints backend detectados, sin datos",
        "docs/forms.json                       Formularios y actions detectados",
        "docs/capture_manifest.json            Resumen de captura",
        "docs/ARCHITECTURE.md                  Este documento",
        "```",
        "",
        "## Patron tecnico observado",
        "",
        "- Aplicacion bajo prefijo `/SIMCORE_WEB/`.",
        "- Rutas con forma ASP.NET MVC: `/SIMCORE_WEB/{Controlador}/{Accion}`.",
        "- Login por `POST /SIMCORE_WEB/Login/Index` y sesion por cookies del servidor.",
        "- Vistas HTML servidas por controladores MVC.",
        "- JS de pantalla en `/SIMCORE_WEB/Scripts/Views/*_Index.js`.",
        "- Uso intensivo de jQuery/AJAX/DataTables para cargar tablas desde endpoints como `Obtener`, `Guardar`, `Eliminar`, `Actualizar`.",
        "- Bundles publicos: `/Content/PluginsCSS`, `/Content/PluginsJS`, `/Content/css`, `/bundles/jquery`, `/bundles/bootstrap`, `/bundles/modernizr`.",
        "",
        "## Resumen cuantitativo",
        "",
        f"- Paginas HTML almacenadas: {len(visible_pages)}",
        f"- Paginas con error o no HTML: {len(errors)}",
        f"- Assets descargados o intentados: {len(asset_report)}",
        f"- Assets con error: {len(asset_errors)}",
        f"- Endpoints backend detectados: {len(endpoint_report)}",
        f"- Formularios detectados: {len(forms)}",
        "",
        "## Controladores con mas endpoints detectados",
        "",
    ]
    for controller, count in controllers.most_common(20):
        lines.append(f"- `{controller}`: {count}")
    if not controllers:
        lines.append("- No se detectaron endpoints.")

    lines.extend(["", "## Paginas HTML capturadas", ""])
    for page in visible_pages:
        lines.append(f"- `{page['path']}` -> `{page['local_file']}`")

    if errors:
        lines.extend(["", "## Paginas no capturadas o con error", ""])
        for page in errors:
            status = page.get("status")
            ctype = page.get("content_type", "")
            lines.append(f"- `{page['path']}` -> {status} {ctype}")

    lines.extend(["", "## Endpoints backend detectados", ""])
    for endpoint in endpoint_report[:200]:
        source = endpoint.get("source", "")
        lines.append(f"- `{endpoint['path']}` ({source})")
    if len(endpoint_report) > 200:
        lines.append(f"- ... {len(endpoint_report) - 200} endpoints adicionales en `docs/endpoints.json`")

    lines.extend(["", "## Recomendacion para reconectar en casa", ""])
    lines.extend([
        "1. Mantener el prefijo `/SIMCORE_WEB/` en el proxy o servidor local.",
        "2. Reproducir primero endpoints `Obtener` con datos ficticios del NAS.",
        "3. Luego implementar `Guardar`, `Actualizar` y `Eliminar` contra la base simulada.",
        "4. Usar los JS de `mirror/SIMCORE_WEB/Scripts/Views/` para ver que campos espera cada pantalla.",
        "5. No usar datos reales de pacientes en pruebas fuera del laboratorio.",
    ])

    write_text(capture / "docs" / "ARCHITECTURE.md", "\n".join(lines) + "\n")


def main() -> None:
    if not USER or not PASSWORD:
        raise SystemExit("Define SIMCORE_SOURCE_USER y SIMCORE_SOURCE_PASS.")

    capture = role_dir()
    (capture / "docs").mkdir(parents=True, exist_ok=True)
    (capture / "mirror" / "_pages").mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    login_url = urljoin(BASE_URL, "Login/Index")
    login = session.post(login_url, data={"user": USER, "pass": PASSWORD}, headers=HEADERS, timeout=30)

    queue: deque[str] = deque()
    seen_pages: set[str] = set()
    for route in SEED_PAGES:
        queue.append(urljoin(BASE_URL, clean_route(route)))

    assets: set[str] = set()
    fetched_assets: set[str] = set()
    page_report: list[dict[str, object]] = []
    asset_report: list[dict[str, object]] = []
    forms: list[dict[str, str]] = []
    endpoint_sources: dict[str, set[str]] = {}
    page_map: dict[str, str] = {}

    while queue:
        url = queue.popleft()
        url, _frag = urldefrag(url)
        path = route_from_url(url)
        if path in seen_pages:
            continue
        seen_pages.add(path)

        try:
            response = session.get(url, headers=HEADERS, timeout=30)
        except requests.RequestException as exc:
            page_report.append({"path": path, "status": "ERROR", "error": str(exc), "stored": False})
            continue

        ctype = response.headers.get("content-type", "")
        item: dict[str, object] = {
            "path": path,
            "url": url,
            "status": response.status_code,
            "content_type": ctype,
            "bytes": len(response.content),
            "stored": False,
        }
        if response.status_code >= 400 or "html" not in ctype.lower():
            if looks_like_backend(path):
                endpoint_sources.setdefault(path, set()).add("GET/no-body")
            page_report.append(item)
            continue

        html = sanitize_text(decode_response(response))
        out_file = page_path(capture, path)
        write_text(out_file, html)
        local_file = str(out_file.relative_to(capture)).replace("\\", "/")
        item["stored"] = True
        item["local_file"] = local_file
        page_report.append(item)

        page_map[path.rstrip("/")] = local_file
        page_map[path if path.endswith("/") else path + "/"] = local_file
        if path.rstrip("/") in {SOURCE_PREFIX.rstrip("/"), SOURCE_PREFIX.rstrip("/") + "/Home/Index"}:
            page_map[SOURCE_PREFIX] = local_file

        for raw_asset in find_assets(html):
            normalized = normalize_url(raw_asset, url)
            if normalized:
                assets.add(normalized)

        for form in find_forms(html, url):
            forms.append(form)
            if form["method"] != "GET" or looks_like_backend(form["action"]):
                endpoint_sources.setdefault(form["action"], set()).add(f"FORM/{form['method']}")

        for endpoint in find_backend_endpoints(html, url):
            endpoint_sources.setdefault(endpoint, set()).add(f"HTML/{path}")

        for raw_link in find_page_links(html):
            normalized = normalize_url(raw_link, url)
            if not normalized:
                continue
            link_path = route_from_url(normalized)
            if looks_like_backend(link_path):
                endpoint_sources.setdefault(link_path, set()).add(f"LINK/{path}")
                continue
            if should_try_as_page(normalized) and link_path not in seen_pages:
                queue.append(normalized)

    css_to_scan: list[str] = []
    for asset_url in sorted(assets):
        result = fetch_asset(session, capture, asset_url, fetched_assets)
        if not result:
            continue
        asset_report.append(result)
        ctype = str(result.get("content_type", "")).lower()
        if result.get("status") == 200 and ("css" in ctype or "/Content/" in str(result.get("path", ""))):
            css_to_scan.append(asset_url)

        if result.get("status") == 200 and "/Scripts/Views/" in str(result.get("path", "")):
            local_file = result.get("local_file")
            if local_file:
                js_path = capture / str(local_file)
                js_text = js_path.read_text(encoding="utf-8", errors="replace")
                for endpoint in find_backend_endpoints(js_text, asset_url):
                    endpoint_sources.setdefault(endpoint, set()).add(f"JS/{result.get('path')}")

    for css_url in css_to_scan:
        css_path = local_asset_path(capture, css_url)
        if not css_path.exists():
            continue
        css_text = css_path.read_text(encoding="utf-8", errors="replace")
        for ref in find_css_urls(css_text):
            normalized = normalize_url(ref, css_url)
            if normalized:
                result = fetch_asset(session, capture, normalized, fetched_assets)
                if result:
                    asset_report.append(result)

    endpoint_report = [
        {"path": path, "source": ", ".join(sorted(sources))}
        for path, sources in sorted(endpoint_sources.items())
    ]

    manifest = {
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "role": ROLE,
        "source_base_url": BASE_URL,
        "login_status": login.status_code,
        "pages": page_map,
        "page_count": len([p for p in page_report if p.get("stored")]),
        "page_attempts": len(page_report),
        "asset_count": len([a for a in asset_report if a.get("status") == 200]),
        "asset_attempts": len(asset_report),
        "endpoint_count": len(endpoint_report),
        "notes": [
            "Backend source code is not available over HTTP.",
            "Data/list endpoint bodies were not stored to avoid patient data.",
            "Session identifiers and 8-digit numeric identifiers were sanitized in captured HTML/view JS.",
        ],
    }

    write_text(capture / "docs" / "capture_manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
    write_text(capture / "docs" / "routes.json", json.dumps(page_report, indent=2, ensure_ascii=False))
    write_text(capture / "docs" / "assets.json", json.dumps(asset_report, indent=2, ensure_ascii=False))
    write_text(capture / "docs" / "endpoints.json", json.dumps(endpoint_report, indent=2, ensure_ascii=False))
    write_text(capture / "docs" / "forms.json", json.dumps(forms, indent=2, ensure_ascii=False))
    build_architecture_md(capture, ROLE, page_report, endpoint_report, asset_report, forms)

    print(json.dumps({
        "role": ROLE,
        "capture": str(capture),
        "pages": manifest["page_count"],
        "page_attempts": manifest["page_attempts"],
        "assets": manifest["asset_count"],
        "asset_attempts": manifest["asset_attempts"],
        "endpoints": manifest["endpoint_count"],
        "login_status": login.status_code,
    }, indent=2))


if __name__ == "__main__":
    main()
