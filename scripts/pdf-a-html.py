"""Convierte la exportación PDF de un tema (Claude Docs) en HTML para scripts/importar-tema.py.

Se usa con los temas cortos, cuya exportación HTML llega dentro de la conversación y no se
guarda en disco; la exportación PDF, más grande, sí se guarda.

Uso: python3 -I scripts/pdf-a-html.py ENTRADA SALIDA.html
ENTRADA: el .pdf, o el archivo que guardó la herramienta de exportación (JSON con bytes_b64).

Reconoce la tipografía de las exportaciones de Claude Docs: título 24 pt, apartados 16,5 pt,
subapartados 13,5 pt, texto 12 pt, tablas 11,3 pt, viñetas en DejaVuSans y negrita en Semibold.
"""
import base64
import html
import io
import json
import re
import sys
from pathlib import Path

import pdfplumber

H1, H2, H3, TABLA = 24.0, 16.5, 13.5, 11.3


def abrir(ruta: Path) -> bytes:
    datos = ruta.read_bytes()
    if datos[:4] == b"%PDF":
        return datos
    d = json.loads(datos.decode("utf-8"))
    if isinstance(d, list):
        d = json.loads(d[0]["text"])
    b = base64.b64decode(d["data"]["bytes_b64"])
    if len(b) != d["data"]["bytes"]:
        sys.exit("El PDF decodificado no tiene el tamaño esperado.")
    return b


def estilo(fontname: str) -> str:
    f = fontname.split("+")[-1]
    s = ""
    if "Semibold" in f or "Bold" in f:
        s += "b"
    if "Italic" in f:
        s += "i"
    return s


def runs_html(words) -> str:
    """Palabras de una línea (o de varias) -> HTML con <strong>/<em>.

    Entre dos palabras se pone espacio solo si en el PDF hay hueco (o salto de línea):
    así «Búsqueda (fetch):» no se convierte en «Búsqueda ( fetch ):».
    """
    out, cur, buf, prev = [], None, "", None
    for w in words:
        st = estilo(w["fontname"])
        sep = ""
        if prev is not None:
            mismo_renglon = abs(w["top"] - prev["top"]) < 3
            sep = " " if (not mismo_renglon or w["x0"] - prev["x1"] > 2.0) else ""
            # Palabra con guion partida a final de línea («running-» + «config»).
            if not mismo_renglon and re.search(r"\w-$", prev["text"]):
                sep = ""
        if st != cur and buf:
            out.append((cur, buf))
            buf = ""
        if out and not buf and sep:
            out.append((None, " "))
            sep = ""
        cur = st
        buf += sep + w["text"]
        prev = w
    if buf:
        out.append((cur, buf))
    partes = []
    for st, t in out:
        t = html.escape(t, quote=False)
        if st and "i" in st:
            t = f"<em>{t}</em>"
        if st and "b" in st:
            t = f"<strong>{t}</strong>"
        partes.append(t)
    return "".join(partes)


def lineas(words, vinetas=()):
    """Agrupa palabras en líneas por su posición vertical."""
    words = sorted(words, key=lambda w: (round(w["top"]), w["x0"]))
    res = []
    for w in words:
        if res and abs(res[-1]["top"] - w["top"]) < 3:
            res[-1]["words"].append(w)
        else:
            res.append({"top": w["top"], "bottom": w["bottom"], "words": [w]})
    for l in res:
        l["words"].sort(key=lambda w: w["x0"])
        l["x0"] = l["words"][0]["x0"]
        sizes = [round(w["size"], 1) for w in l["words"] if not w["fontname"].endswith("DejaVuSans")]
        l["size"] = max(set(sizes), key=sizes.count) if sizes else 12.0
        l["bottom"] = max(w["bottom"] for w in l["words"])
        l["vineta"] = any(v[0] < l["x0"] and abs(v[1] - (l["top"] + 3.7)) < 3.5 for v in vinetas)
    return res


def tabla_html(filas) -> str:
    def celda(t):
        return (t or "").strip()  # ya viene en HTML desde runs_html
    h = ["<table>", "<thead><tr>" + "".join(f"<th>{celda(c)}</th>" for c in filas[0]) + "</tr></thead>", "<tbody>"]
    for f in filas[1:]:
        h.append("<tr>" + "".join(f"<td>{celda(c)}</td>" for c in f) + "</tr>")
    h.append("</tbody></table>")
    return "".join(h)


def convertir(pdf_bytes: bytes) -> str:
    bloques = []  # (tipo, datos)
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            todas = [w for w in page.extract_words(extra_attrs=["fontname", "size"], keep_blank_chars=False, use_text_flow=True)
                     if w["size"] >= 7 and w["top"] < page.height - 40]  # sin cabecera ni «Page N»
            vinetas = [(o["x0"], o["top"]) for o in page.objects.get("curve", []) if o["x1"] - o["x0"] < 6 and o["bottom"] - o["top"] < 6]
            # Zonas de tabla: líneas seguidas con letra de tabla (~11,3 pt).
            zonas = []
            for l in lineas(todas):
                if abs(l["size"] - TABLA) < 0.4:
                    if zonas and l["top"] - zonas[-1][1] < 40:
                        zonas[-1][1] = l["bottom"]
                    else:
                        zonas.append([l["top"], l["bottom"]])
            tablas = []
            for z0, z1 in zonas:
                recorte = page.crop((0, max(0, z0 - 12), page.width, min(page.height, z1 + 12)))
                for t in recorte.find_tables():
                    tablas.append(t)
            cajas = [t.bbox for t in tablas]
            dentro = lambda w: any(b[0] - 1 <= w["x0"] and w["x1"] <= b[2] + 1 and b[1] - 1 <= w["top"] and w["bottom"] <= b[3] + 1 for b in cajas)
            words = [w for w in todas if not dentro(w)]
            items = [("linea", l["top"], l) for l in lineas(words, vinetas)]
            def celdas(t):
                filas = []
                for fila in t.rows:
                    f = []
                    for c in fila.cells:
                        if c is None:
                            f.append("")
                            continue
                        ws = [w for w in todas if c[0] - 1 <= w["x0"] and w["x1"] <= c[2] + 1 and c[1] - 1 <= w["top"] and w["bottom"] <= c[3] + 1]
                        ws.sort(key=lambda w: (round(w["top"]), w["x0"]))
                        f.append(runs_html(ws))
                    filas.append(f)
                return filas
            items += [("tabla", t.bbox[1], celdas(t)) for t in tablas]
            items.sort(key=lambda x: x[1])
            for tipo, top, dato in items:
                if tipo == "tabla":
                    filas = [f for f in dato if any((c or "").strip() for c in f)]
                    if not filas:
                        continue
                    # Tabla partida entre páginas: se une a la anterior si tiene las mismas columnas.
                    if bloques and bloques[-1][0] == "tabla" and len(bloques[-1][1][0]) == len(filas[0]):
                        if filas[0] == bloques[-1][1][0]:
                            filas = filas[1:]  # cabecera repetida en la página nueva
                        bloques[-1][1].extend(filas)
                    else:
                        bloques.append(("tabla", filas))
                else:
                    bloques.append(("linea", dato))
    return montar(bloques)


def montar(bloques) -> str:
    out, para, lista = [], None, None  # para: {"words": [...], "x0", "bottom", "size"}; lista: {"tipo", "items": [para...]}

    def cerrar_para():
        nonlocal para
        if para is None:
            return
        texto = runs_html(para["words"])
        if lista is not None and para.get("item"):
            lista["items"].append(texto)
        elif lista is not None and lista["items"] and para.get("cont"):
            lista["items"][-1] += " " + texto
        else:
            cerrar_lista()
            out.append(f"<p>{texto}</p>")
        para = None

    def cerrar_lista():
        nonlocal lista
        if lista is None:
            return
        tag = "ol" if lista["tipo"] == "ol" else "ul"
        out.append(f"<{tag}>" + "".join(f"<li><p>{i}</p></li>" for i in lista["items"]) + f"</{tag}>")
        lista = None

    prev_heading = None
    for tipo, d in bloques:
        if tipo == "tabla":
            cerrar_para(); cerrar_lista(); prev_heading = None
            out.append(tabla_html(d))
            continue
        l = d
        size = l["size"]
        texto_linea = " ".join(w["text"] for w in l["words"])
        if size >= H1 - 0.5 or abs(size - H2) < 0.6 or abs(size - H3) < 0.6:
            nivel = 1 if size >= H1 - 0.5 else (2 if abs(size - H2) < 0.6 else 3)
            cerrar_para(); cerrar_lista()
            if prev_heading and prev_heading[0] == nivel and l["top"] - prev_heading[1] < size * 1.8:
                out[-1] = out[-1].replace(f"</h{nivel}>", " " + html.escape(texto_linea, quote=False) + f"</h{nivel}>")
            else:
                out.append(f"<h{nivel}>{html.escape(texto_linea, quote=False)}</h{nivel}>")
            prev_heading = (nivel, l["top"])
            continue
        prev_heading = None
        if size < 10 and "@" in texto_linea:  # línea de fecha y autor
            continue
        words = l["words"]
        primero = words[0]
        es_vineta = l.get("vineta", False)
        m = re.match(r"^(\d{1,2})\.$", primero["text"])
        es_num = bool(m) and len(words) > 1 and words[1]["x0"] - primero["x1"] < 20 and (lista is not None and lista["tipo"] == "ol" or m.group(1) == "1")
        if es_vineta or es_num:
            cerrar_para()
            t = "ol" if es_num else "ul"
            if lista is None or lista["tipo"] != t:
                cerrar_lista()
                lista = {"tipo": t, "items": [], "x0": words[1]["x0"] if len(words) > 1 else primero["x0"]}
            resto = words if es_vineta else words[1:]
            if lista is None or lista["tipo"] != t:
                pass
            lista["x0"] = resto[0]["x0"] if resto else primero["x0"]
            para = {"words": resto, "x0": lista["x0"], "bottom": l["bottom"], "size": size, "item": True}
            continue
        # Continuación del párrafo o del elemento de lista anterior.
        if para is not None and l["top"] - para["bottom"] < size * 0.9 and abs(l["x0"] - para["x0"]) < 4:
            para["words"].extend(words)
            para["bottom"] = l["bottom"]
            continue
        cerrar_para()
        if lista is not None and abs(l["x0"] - lista["x0"]) < 4:
            para = {"words": words, "x0": l["x0"], "bottom": l["bottom"], "size": size, "cont": True}
            continue
        cerrar_lista()
        para = {"words": words, "x0": l["x0"], "bottom": l["bottom"], "size": size}
    cerrar_para(); cerrar_lista()
    return "\n".join(out) + "\n"


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    salida = Path(sys.argv[2])
    salida.write_text(convertir(abrir(Path(sys.argv[1]))), encoding="utf-8")
    print(f"{salida}: {salida.stat().st_size} bytes")


if __name__ == "__main__":
    main()
