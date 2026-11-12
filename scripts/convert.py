"""Convierte temario/tests-tai.json (exámenes oficiales del INAP) en bancos de la web.

Cada examen da tres bancos: el cuestionario (primera parte + reservas) y cada supuesto
práctico (con sus reservas). Uso: python3 -I convert.py tests-tai.json ../oposiciones-tai/data/bancos
"""
import json
import sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
d = json.loads(src.read_text(encoding="utf-8"))
LET = "abcd"
MIN_POR_PREGUNTA = 1.2  # 120 minutos para 100 preguntas en el turno libre

TURNO = {"libre": "libre", "promocion_interna": "promoción interna"}
BLOQUES = [
    ("cuestionario", "Cuestionario", ["primera", "primera_reserva"]),
    ("supuesto1", "Supuesto práctico I", ["supuesto1", "supuesto1_reserva"]),
    ("supuesto2", "Supuesto práctico II", ["supuesto2", "supuesto2_reserva"]),
]
PREF = {"primera": "p", "primera_reserva": "pr", "supuesto1": "s1", "supuesto1_reserva": "s1r",
        "supuesto2": "s2", "supuesto2_reserva": "s2r"}

def limpia(s):
    return " ".join(str(s or "").split())

total = 0
written = []
for e in d["examenes"]:
    partes = {p["parte"]: p for p in e["partes"]}
    turno = TURNO.get(e["turno"], e["turno"])
    tid = "libre" if e["turno"] == "libre" else "pi"
    base = f"oficial-{e['anio']}-{tid}" + ("-ext" if e["id"].endswith("ext") else "")
    conv = f"{e['anio']} · {turno}" + (" · extraordinario" if e["id"].endswith("ext") else "")
    for suf, nombre, claves in BLOQUES:
        preguntas = []
        contexto = None
        for k in claves:
            p = partes.get(k)
            if not p:
                continue
            if p.get("contexto"):
                contexto = p["contexto"].strip()
            for q in p["preguntas"]:
                ops = [limpia(q["opciones"].get(l)) for l in LET if q["opciones"].get(l) is not None]
                item = {
                    "id": f"{PREF[k]}{int(q['n']):02d}",
                    "tema": q.get("tema"),
                    "enunciado": limpia(q["enunciado"]),
                    "opciones": ops,
                    "correcta": LET.index(q["correcta"]) if q.get("correcta") in list(LET) else None,
                    "explicacion": None,
                }
                if k.endswith("reserva"):
                    item["reserva"] = True
                if q.get("anulada") or item["correcta"] is None:
                    item["anulada"] = True
                if q.get("modificada_en_definitiva"):
                    item["modificada_en_definitiva"] = True
                if contexto and k.startswith("supuesto"):
                    item["contexto"] = "s" + k[8]
                preguntas.append(item)
        if not preguntas:
            continue
        validas = [q for q in preguntas if not q.get("anulada")]
        bank = {
            "titulo": f"Examen {conv} · {nombre}",
            "fuente": "oficial",
            "examen": e["id"],
            "parte": suf,
            "tema": None,
            "convocatoria": conv,
            "minutos": round(len([q for q in validas if not q.get("reserva")]) * MIN_POR_PREGUNTA),
            "origen": e.get("convocatoria"),
            "url_cuestionario": e.get("url_cuestionario"),
            "url_plantilla": e.get("url_plantilla_definitiva"),
            "contextos": {"s" + suf[-1]: contexto} if contexto and suf.startswith("supuesto") else {},
            "preguntas": preguntas,
        }
        f = out / f"{base}-{suf}.json"
        f.write_text(json.dumps(bank, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        written.append(f.name)
        total += len(preguntas)

print(len(written), "bancos,", total, "preguntas")
