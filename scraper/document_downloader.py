from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import Request, urlopen


def download_document(
    page_url: str,
    download_url: str,
    descripcion: str,
    codigo_necesidad: str,
    output_dir: Path,
) -> dict[str, str]:
    absolute_url = urljoin(page_url, download_url)
    output_dir.mkdir(parents=True, exist_ok=True)

    request = Request(absolute_url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        content = response.read()
        filename = _build_filename(
            descripcion=descripcion,
            codigo_necesidad=codigo_necesidad,
            download_url=absolute_url,
            content_disposition=response.headers.get("Content-Disposition"),
        )

    local_path = output_dir / filename
    local_path.write_bytes(content)
    return {
        "download_url": absolute_url,
        "nombre_archivo": filename,
        "ruta_local": str(local_path),
    }


def _build_filename(
    descripcion: str,
    codigo_necesidad: str,
    download_url: str,
    content_disposition: str | None,
) -> str:
    extension = _extract_extension(content_disposition, download_url)
    base_name = f"{_slug(descripcion)}_{_slug(codigo_necesidad)}"
    return f"{base_name}{extension}"


def _extract_extension(content_disposition: str | None, download_url: str) -> str:
    if content_disposition:
        match = re.search(r"filename\*?=(?:UTF-8''|[\"']?)(?P<filename>[^\"';]+)", content_disposition, re.IGNORECASE)
        if match:
            suffix = Path(unquote(match.group("filename"))).suffix
            if suffix:
                return suffix

    suffix = Path(urlparse(download_url).path).suffix
    return suffix or ".bin"


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "archivo"
