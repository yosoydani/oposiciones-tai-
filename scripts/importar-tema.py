"""Importa un tema del temario a la web a partir de su exportación HTML de Claude Docs.

Uso:
  python3 -I scripts/importar-tema.py NN ENTRADA REV

ENTRADA puede ser:
  - el HTML exportado (archivo .html),
  - el Markdown exportado desde el menú Exportar del doc (archivo .md; se convierte con pandoc),
  - un archivo con solo el base64 de la exportación (bytes_b64),
  - el JSON del resultado de la herramienta de exportación tal cual se guardó en disco
    (con "bytes_b64" dentro, aunque venga envuelto en [{"type":"text","text":"{...}"}]).
REV es el número de revisión del doc que devuelve la exportación ("rev").

Escribe data/temas/tNN.html (limpio, sin la línea de autor ni el test del doc, que ya está
en la web como test interactivo) y actualiza data/temas/index.json.
"""
import base64
import datetime
import html
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def leer_html(ruta: Path) -> str:
    crudo = ruta.read_text(encoding="utf-8").strip()
    if ruta.suffix.lower() in (".md", ".markdown"):
        # Exportación a Markdown desde el menú del doc: se convierte con pandoc.
        import subprocess
        return subprocess.run(["pandoc", "-f", "gfm", "-t", "html", str(ruta)], check=True, capture_output=True, text=True).stdout
    if crudo.lstrip().startswith("<"):
        return crudo
    b64 = None
    if crudo.startswith("[") or crudo.startswith("{"):
        datos = json.loads(crudo)
        if isinstance(datos, list):
            datos = json.loads(datos[0]["text"])
        b64 = datos["data"]["bytes_b64"]
        esperado = datos["data"].get("bytes")
    else:
        b64 = re.sub(r"\s+", "", crudo)
        esperado = None
    contenido = base64.b64decode(b64, validate=True)
    if esperado is not None and len(contenido) != esperado:
        sys.exit(f"Tamaño decodificado {len(contenido)} distinto de {esperado}: la exportación está corrupta.")
    return contenido.decode("utf-8")


def limpiar(doc: str) -> tuple[str, str]:
    # Título: el primer h1.
    m = re.search(r"<h1[^>]*>(.*?)</h1>", doc, re.S)
    titulo = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""
    if m:
        doc = doc[: m.start()] + doc[m.end():]
    # Línea de fecha y autor (chips de fecha y mención) justo bajo el título.
    doc = re.sub(r"<p>\s*<time[^>]*>.*?</time>\s*·?\s*<span data-atom=\"mention\"[^>]*>.*?</span>\s*</p>", "", doc, count=1, flags=re.S)
    # La misma línea en la exportación a Markdown («Nov 11, 2026 · @Nombre»).
    doc = re.sub(r"<p>\s*\w{3,10}\.? \d{1,2}, \d{4}\s*·\s*@[^<]*</p>", "", doc, count=1)
    # Menciones sueltas: se dejan como texto plano sin el identificador interno.
    doc = re.sub(r"<span data-atom=\"mention\"[^>]*>.*?</span>", "", doc, flags=re.S)
    # El test del doc (desde su h2 hasta el final): en la web es interactivo.
    t = re.search(r"<h2[^>]*>[^<]*(?:Test|test)[^<]*</h2>", doc)
    if t:
        doc = doc[: t.start()]
    # Seguridad básica: nada ejecutable.
    doc = re.sub(r"<script\b.*?</script>", "", doc, flags=re.S | re.I)
    doc = re.sub(r"\son\w+=\"[^\"]*\"", "", doc, flags=re.I)
    doc = re.sub(r"href=\"\s*javascript:[^\"]*\"", 'href="#"', doc, flags=re.I)
    # Enlaces externos en pestaña nueva.
    doc = re.sub(r"<a href=\"(https?://[^\"]+)\">", r'<a href="\1" target="_blank" rel="noopener">', doc)
    return titulo, doc.strip() + "\n"


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    nn, entrada, rev = int(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
    titulo, cuerpo = limpiar(leer_html(entrada))
    if len(cuerpo) < 2000:
        sys.exit(f"El tema {nn} ha quedado con solo {len(cuerpo)} caracteres: revisa la exportación.")
    destino = RAIZ / "data" / "temas"
    destino.mkdir(parents=True, exist_ok=True)
    (destino / f"t{nn:02d}.html").write_text(cuerpo, encoding="utf-8")
    idx_ruta = destino / "index.json"
    idx = json.loads(idx_ruta.read_text(encoding="utf-8")) if idx_ruta.exists() else {}
    idx[str(nn)] = {"titulo": titulo, "rev": rev, "actualizado": datetime.date.today().isoformat(), "caracteres": len(cuerpo)}
    idx_ruta.write_text(json.dumps(dict(sorted(idx.items(), key=lambda kv: int(kv[0]))), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"t{nn:02d}.html: {titulo} · rev {rev} · {len(cuerpo)} caracteres")


if __name__ == "__main__":
    main()
